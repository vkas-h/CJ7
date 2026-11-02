
import json

from core.context import context_manager
from utils.plugin_loader import load_plugins
from core.tool import commands_to_tools
from services.llm import stream_with_model
from core.action import Action
from core.dispatcher import dispatch
from core.permissions import request_permission
from core.progress import Progress
from core.planner import PLAN_TOOL
from core.reasoning import ReasoningRouter
from core.message import Message
from core.execution_guard import ExecutionGuard
from services.tts import speak


MAX_TOOL_RESULT_CHARS = 2000


class Agent:
    def __init__(self, commands=None, tool_context=None):
        self.commands = (
            commands if commands is not None else load_plugins()
        )

        self.tools = commands_to_tools(self.commands)
        self.tools.append(PLAN_TOOL)

        self.progress = Progress()
        self.reasoning_router = ReasoningRouter()
        self.tool_context = tool_context

    # --------------------------------------------------
    # REASONING
    # --------------------------------------------------

    def think_stream(self, messages):
        policy = self.reasoning_router.decide(messages)

        print(f"[REASONING] {policy.level.value}")

        return stream_with_model(
            messages=messages,
            tools=self.tools,
            reasoning=policy.think,
            effort=policy.effort,
        )

    # --------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------

    @staticmethod
    def persist_transcript(callback):
        if callback is not None:
            callback()

    # --------------------------------------------------
    # TOOL HOOKS
    # --------------------------------------------------

    def before_tool_execution(self, tool_name, arguments):
        print(f"[HOOK] Starting tool: {tool_name}")

    def after_tool_execution(self, tool_name, result):
        status = "SUCCESS" if result.get("success") else "FAILED"
        print(f"[HOOK] Tool {tool_name}: {status}")

    # --------------------------------------------------
    # RESULT LIMITING
    # --------------------------------------------------

    @staticmethod
    def limit_result_text(value):
        if not isinstance(value, str):
            return value

        if len(value) <= MAX_TOOL_RESULT_CHARS:
            return value

        omitted = len(value) - MAX_TOOL_RESULT_CHARS

        return (
            value[:MAX_TOOL_RESULT_CHARS]
            + f"\n\n[OUTPUT TRUNCATED: {omitted} characters omitted]"
        )

    # --------------------------------------------------
    # TOOL CALL NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def get_tool_name(tool_call):
        return tool_call.function.name

    @staticmethod
    def get_tool_arguments(tool_call):
        arguments = getattr(tool_call.function, "arguments", {})

        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be a JSON object.")

        return arguments

    @staticmethod
    def serialize_tool_calls(tool_calls):
        serialized = []

        for tool_call in tool_calls:
            serialized.append({
                "function": {
                    "name": Agent.get_tool_name(tool_call),
                    "arguments": Agent.get_tool_arguments(tool_call),
                }
            })

        return serialized

    # --------------------------------------------------
    # TOOL EXECUTION
    # --------------------------------------------------

    def execute_tool(self, tool_name, arguments):
        if tool_name == "create_plan":
            try:
                self.progress.create_plan(arguments.get("steps", []))

                return {
                    "success": True,
                    "output": "Plan created successfully.",
                    "error": None,
                }
            except Exception as error:
                return {
                    "success": False,
                    "output": None,
                    "error": f"Invalid plan: {error}",
                }

        command = self.commands.get(tool_name)

        if command is None:
            return {
                "success": False,
                "output": None,
                "error": f"Unknown tool: {tool_name}",
            }

        if not request_permission(
            command,
            arguments,
            self.tool_context,
        ):
            return {
                "success": False,
                "output": None,
                "error": f"Permission denied for tool: {tool_name}",
            }

        self.before_tool_execution(tool_name, arguments)

        action = Action(
            type=tool_name,
            arguments=arguments,
        )

        result = dispatch(action, self.commands)

        result.output = self.limit_result_text(result.output)
        result.error = self.limit_result_text(result.error)

        output = result.to_dict()
        self.after_tool_execution(tool_name, output)

        return output

    # --------------------------------------------------
    # TRANSCRIPT HELPERS
    # --------------------------------------------------

    def append_tool_result(
        self,
        messages,
        tool_name,
        result,
        on_update,
    ):
        content = json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )

        messages.append(
            Message(
                role="tool",
                content=content,
                metadata={
                    "tool_name": tool_name,
                    "provenance": {
                        "source_type": "tool",
                        "source_ref": tool_name,
                    },
                },
            )
        )

        self.persist_transcript(on_update)

    def append_assistant_tool_request(
        self,
        messages,
        content,
        serialized_tool_calls,
        on_update,
    ):
        messages.append(
            Message(
                role="assistant",
                content=content or "",
                metadata={
                    "tool_calls": serialized_tool_calls,
                    "provenance": {
                        "source_type": "assistant",
                        "source_ref": "model_tool_call",
                    },
                },
            )
        )

        self.persist_transcript(on_update)

    # --------------------------------------------------
    # MODEL STREAMING
    # --------------------------------------------------

    def collect_model_response(self, llm_messages):
        stream = self.think_stream(llm_messages)

        thinking_started = False
        answer_started = False

        full_content = ""
        tool_calls = []

        for chunk in stream:
            message = chunk.message

            thinking = getattr(message, "thinking", None)

            if thinking:
                if not thinking_started:
                    print("\n[THINKING]\n")
                    thinking_started = True

                print(thinking, end="", flush=True)

            content = getattr(message, "content", None)

            if content:
                if not answer_started:
                    if thinking_started:
                        print("\n")

                    print("[ANSWER]\n")
                    answer_started = True

                print(content, end="", flush=True)
                full_content += content

            chunk_tool_calls = getattr(
                message,
                "tool_calls",
                None,
            )

            if chunk_tool_calls:
                tool_calls.extend(chunk_tool_calls)

        print("\n")

        return full_content, tool_calls

    # --------------------------------------------------
    # MAIN AGENT LOOP
    # --------------------------------------------------

    def run(self, messages, on_update=None, session_id=None):
        self.progress.finish()

        guard = ExecutionGuard()
        recovery_used = False

        system_prompt = """
You are CJ7, a desktop AI assistant.

You can answer normally or use tools.

Rules:

1. Simple conversational questions:
   - Answer directly.
   - Do not create a plan.
   - Do not use tools unless necessary.

2. One simple action:
   - Use the required tool directly.
   - Do not create a plan.

3. Multiple meaningful steps:
   - First call create_plan.
   - Create 2 to 5 concise phases.
   - Then perform the work.
   - Update your approach when a tool fails.

4. Execution:
   - Inspect tool results before deciding what to do next.
   - Do not repeat a tool call with the same arguments when its
     previous result has not changed.
   - If an action fails, diagnose the failure and try a meaningfully
     different approach when possible.
   - Never claim an action succeeded unless its tool result confirms it.
   - Do not claim a task is complete while required work remains.
   - If the task cannot be completed, explain what failed and what
     remains unfinished.

5. Planning:
   - A plan describes meaningful task phases, not every individual
     tool call.
   - Do not recreate the plan after every tool call.
   - A plan is guidance, not permission to bypass tool permissions.

6. Safety:
   - Tool permissions are enforced by CJ7.
   - Never attempt to bypass a denied action.
   - Ask the user when required information or approval is missing.

Do not expose private chain-of-thought.
"""

        while True:
            # Rebuild the model context from the authoritative transcript.
            # This also allows context compaction to take effect between
            # model/tool cycles.
            llm_messages = context_manager.prepare_messages(
                transcript=messages,
                system_prompt=system_prompt,
                tools=self.tools,
                session_id=session_id,
            )

            full_content, tool_calls = self.collect_model_response(
                llm_messages
            )

            # No tool calls means the model has produced its final answer.
            if not tool_calls:
                self.progress.finish()

                final_content = full_content.strip()

                if final_content:
                    speak(final_content)

                return final_content or (
                    "I could not produce a response for that request."
                )

            # Validate and serialize the complete batch before execution.
            try:
                serialized_tool_calls = self.serialize_tool_calls(
                    tool_calls
                )
            except Exception as error:
                return f"Invalid tool-call response: {error}"

            self.append_assistant_tool_request(
                messages=messages,
                content=full_content,
                serialized_tool_calls=serialized_tool_calls,
                on_update=on_update,
            )

            # Preflight the whole batch. No tool in this batch runs if
            # any call is a repeated action that the guard has blocked.
            blocked_calls = []

            for tool_call in tool_calls:
                tool_name = self.get_tool_name(tool_call)
                arguments = self.get_tool_arguments(tool_call)

                diagnostic = guard.should_block(
                    tool_name,
                    arguments,
                )

                if diagnostic:
                    blocked_calls.append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "diagnostic": diagnostic,
                    })

            if blocked_calls:
                if recovery_used:
                    terminal_message = (
                        "I stopped this request because the same "
                        "tool-call loop continued after a recovery "
                        "attempt. No further repeated actions were run."
                    )

                    for tool_call in tool_calls:
                        tool_name = self.get_tool_name(tool_call)
                        arguments = self.get_tool_arguments(tool_call)

                        diagnostic = guard.should_block(
                            tool_name,
                            arguments,
                        )

                        result = {
                            "success": False,
                            "output": None,
                            "error": (
                                diagnostic
                                or "Skipped because another call in "
                                   "the batch triggered loop protection."
                            ),
                        }

                        self.append_tool_result(
                            messages,
                            tool_name,
                            result,
                            on_update,
                        )

                    self.progress.finish()
                    return terminal_message

                # One recovery opportunity per user request.
                recovery_used = True

                blocked_by_name = {
                    item["tool_name"]: item["diagnostic"]
                    for item in blocked_calls
                }

                for tool_call in tool_calls:
                    tool_name = self.get_tool_name(tool_call)

                    result = {
                        "success": False,
                        "output": None,
                        "error": (
                            blocked_by_name.get(tool_name)
                            or (
                                "This tool batch was not executed because "
                                "another call triggered loop protection. "
                                "Choose a different approach."
                            )
                        ),
                    }

                    self.append_tool_result(
                        messages,
                        tool_name,
                        result,
                        on_update,
                    )

                # The next model response may recover, ask the user,
                # or provide an honest explanation.
                continue
            
            # Execute the batch in order and persist each result.
            cycle_diagnostic = None

            for index, tool_call in enumerate(tool_calls):
                tool_name = self.get_tool_name(tool_call)
                arguments = self.get_tool_arguments(tool_call)

                if tool_name != "create_plan":
                    self.progress.start_tool_step(tool_name)

                result = self.execute_tool(
                    tool_name,
                    arguments,
                )

                if tool_name != "create_plan":
                    self.progress.complete_tool_step(
                        success=result.get("success", False)
                    )

                cycle_diagnostic = guard.record_outcome(
                    tool_name,
                    arguments,
                    result,
                )

                if cycle_diagnostic:
                    # Preserve the real tool result while informing
                    # the model why execution is being interrupted.
                    result["guard_warning"] = cycle_diagnostic

                self.append_tool_result(
                    messages,
                    tool_name,
                    result,
                    on_update,
                )

                if cycle_diagnostic:
                    # Do not execute the remainder of a batch after
                    # detecting a repeating sequence.
                    for skipped_call in tool_calls[index + 1:]:
                        skipped_name = self.get_tool_name(skipped_call)

                        self.append_tool_result(
                            messages,
                            skipped_name,
                            {
                                "success": False,
                                "output": None,
                                "error": (
                                    "Skipped because a repeating "
                                    "tool-call sequence was detected."
                                ),
                            },
                            on_update,
                        )

                    break

            if cycle_diagnostic:
                if recovery_used:
                    self.progress.finish()
                    return (
                        "I stopped this request because a repeating "
                        "tool-call sequence continued after a recovery "
                        "attempt. No further calls in that sequence "
                        "were executed."
                    )

                recovery_used = True
                continue
