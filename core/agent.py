from utils.plugin_loader import load_plugins
from core.tool import commands_to_tools
from services.llm import stream_with_model
from core.action import Action
from core.dispatcher import dispatch
from core.permissions import request_permission
from core.progress import Progress
from core.planner import PLAN_TOOL
from core.reasoning import ReasoningRouter , ReasoningLevel
# from ollama import chat
from services.tts import speak

MAX_TOOL_RESULT_CHARS = 8000



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

    def describe_tool(self, tool_call):
        tool_name = tool_call.function.name

        descriptions = {
            "search": "Searching the project",
            "openfile": "Opening the file",
            "readfile": "Reading the file",
            "createfile": "Creating the file",
            "createfolder": "Creating the folder",
            "delete": "Deleting the file",
            "open": "Opening the application",
            "remind": "Setting the reminder",
            "notes": "Managing your notes",
            "session": "Managing saved sessions",
            "latestsession": "Checking the latest session",
            "loadsession": "Loading the session",
            "renamesession": "Renaming the session",
            "time": "Checking the time",
            "volume": "Changing the volume",
            "volumeup": "Increasing the volume",
            "volumedown": "Decreasing the volume",
            "mute": "Changing mute state",
            "brightness": "Changing the brightness",
            "brightnessup": "Increasing the brightness",
            "brightnessdown": "Decreasing the brightness",
            "lock": "Locking the computer",
            "sleep": "Putting the computer to sleep",
            "restart": "Restarting the computer",
            "shutdown": "Shutting down the computer",
        }

        return descriptions.get(
            tool_name,
            f"Running {tool_name}"
        )

    
    # def think(self, messages):

    #     policy = self.reasoning_router.decide(messages)

    #     print(
    #         f"[REASONING] "
    #         f"{policy.level.value} "
    #         f"(soft budget: {policy.soft_budget})"
    #     )

    #     return chat_with_model(
    #         messages=messages,
    #         tools=self.tools,
    #         reasoning=policy.think,
    #         effort=policy.effort
    #     )

    def think_stream(self, messages):

        policy = self.reasoning_router.decide(messages)

        print(
            f"[REASONING] "
            f"{policy.level.value} "
            f"(soft budget: {policy.soft_budget})"
        )

        return stream_with_model(
            messages=messages,
            tools=self.tools,
            reasoning=policy.think,
            effort=policy.effort
        )


    def before_tool_execution(self, tool_name, arguments):
        """
        Runs after permission approval and before command dispatch.
        """
        print(f"[HOOK] Starting tool: {tool_name}")


    def after_tool_execution(self, tool_name, result):
            """
            Runs after command dispatch has returned a Result.
            """
            status = "SUCCESS" if result.success else "FAILED"
            print(f"[HOOK] Tool {tool_name}: {status}")
    
    def limit_result_text(self, text):
        if not isinstance(text, str):
            return text

        if len(text) <= MAX_TOOL_RESULT_CHARS:
            return text

        omitted = len(text) - MAX_TOOL_RESULT_CHARS

        return (
            text[:MAX_TOOL_RESULT_CHARS]
            + f"\n\n[OUTPUT TRUNCATED: {omitted} characters omitted]"
        )


    
    def execute_tool(self, tool_call):

        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        if tool_name == "create_plan":
            steps = arguments.get("steps", [])

            self.progress.create_plan(steps)

            return {
                "success": True,
                "output": "Plan created successfully."
            }

        command = self.commands.get(tool_name)

        if command is None:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

        if not request_permission(
            command,
            arguments,
            self.tool_context
        ):
            return {
                "success": False,
                "output": None,
                "error": f"Permission denied for tool: {tool_name}",
            }

        # Hook 1: run before dispatch.
        self.before_tool_execution(tool_name, arguments)

        action = Action(
            type=tool_name,
            arguments=arguments,
        )

        result = dispatch(action, self.commands)

        # Limit returned text before sending it to the model.
        result.output = self.limit_result_text(result.output)
        result.error = self.limit_result_text(result.error)

        # Hook 2: run after dispatch and output processing.
        self.after_tool_execution(tool_name, result)

        return result.to_dict()


    def run(self, messages):


        llm_messages = [

            {
                "role": "system",


                "content": """
                You are CJ7, a desktop AI assistant.

                You have access to normal tools and an internal tool called
                create_plan.

                Rules:

                1. For simple conversational questions:
                - Answer directly.
                - Do not create a plan.
                - Do not use tools unless necessary.

                2. For a task requiring only one simple action:
                - Use the required tool directly.
                - Do not create a plan.

                3. For a task requiring multiple meaningful steps:
                - FIRST call create_plan.
                - Give 2 to 5 concise meaningful task phases.
                - Then perform the required tools.

                The plan should describe the user's task, not raw tool calls.

                Example:

                User:
                "Read agent.py, inspect progress.py, and explain how they work together."

                Good plan:

                create_plan(
                    steps=[
                {
                    "type": "tool",
                    "description": "Read core/agent.py"
                },
                {
                    "type": "tool",
                    "description": "Read core/progress.py"
                },
                {
                    "type": "analysis",
                    "description": "Analyze how Agent and Progress interact"
                },
                {
                    "type": "response",
                    "description": "Explain the integration"
                }
                
                )

                Do not expose chain-of-thought or internal reasoning. """

            }
        ]

        llm_messages += [
            {
                "role": message.role,
                "content": message.content
            }
            
            for message in messages
        ]

        max_steps = 10

        for step in range(max_steps):

            stream = self.think_stream(llm_messages)

            thinking_started = False
            answer_started = False

            full_thinking = ""
            full_content = ""
            tool_calls = []

            # --------------------------------
            # STREAM MODEL RESPONSE
            # --------------------------------

            for chunk in stream:

                message = chunk.message

                # --------------------------------
                # THINKING STREAM
                # --------------------------------

                thinking = getattr(message, "thinking", None)

                if thinking:

                    if not thinking_started:

                        print("\n[THINKING]\n")
                        thinking_started = True

                    print(
                        thinking,
                        end="",
                        flush=True
                    )

                    full_thinking += thinking

                # --------------------------------
                # ANSWER STREAM
                # --------------------------------

                content = getattr(message, "content", None)

                if content:

                    if not answer_started:

                        if thinking_started:
                            print("\n")

                        print("[ANSWER]\n")
                        answer_started = True

                    print(
                        content,
                        end="",
                        flush=True
                    )

                    full_content += content

                # --------------------------------
                # TOOL CALLS
                # --------------------------------

                chunk_tool_calls = getattr(
                    message,
                    "tool_calls",
                    None
                )

                if chunk_tool_calls:
                    tool_calls.extend(chunk_tool_calls)

            print("\n")

            # --------------------------------
            # BUILD ASSISTANT MESSAGE
            # --------------------------------

            assistant_message = {
                "role": "assistant",
                "content": full_content,
            }

            if full_thinking:
                assistant_message["thinking"] = full_thinking

            if tool_calls:
                assistant_message["tool_calls"] = tool_calls

            llm_messages.append(assistant_message)

            # --------------------------------
            # FINAL RESPONSE
            # --------------------------------

            if not tool_calls:

                self.progress.finish()
                speak(full_content)

                return full_content

            # --------------------------------
            # TOOL EXECUTION
            # --------------------------------

            for tool_call in tool_calls:

                tool_name = tool_call.function.name

                # create_plan is an internal operation
                if tool_name == "create_plan":

                    result = self.execute_tool(tool_call)

                else:

                    self.progress.start_step()

                    result = self.execute_tool(tool_call)

                llm_messages.append({
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": str(result)
                })

        self.progress.finish()

        return "I couldn't complete the request within the allowed tool steps."