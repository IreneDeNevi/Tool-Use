from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

cliente = OpenAI()

def get_temperature(city:str) -> float:
    # response = cliente.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": "You are a helpful assistant that provides the current temperature of a given city."
    #         },
    #         {
    #             "role": "user",
    #             "content": f"What is the current temperature in {city}?"
    #         }
    #     ]
    # )
    # return response.choices[0].message.content.strip()
    print(f"Fetching temperature for {city}...")
    return 20.0  # Placeholder value for temperature

def main():
    user_input = input("Your question: ")
    prompt = f"""
    You are a helpful assistant. Answer the user's question in a friendly way.

    You can also use tools if you feel like they help you provide a better answer:
        - get_temperature(city: str) -> float: This tool returns the current temperature of a given city. You can use it by calling get_temperature("City Name").

    If you want to use one of these tools, you should output the tool name and its arguments in the following format:
        tool_name: arg1, arg2, ...
    For example:
        get_temperature: New York

    with that in mind, answear the user's question: 
        <user-question>
        {user_input}
        </user-question>

    If you request a tool, please output ONLY the tool call (as described above) and nothing else. 
    """
    response = cliente.chat.completions.create(
        model="gpt-4o",
        input=prompt,
    )
    reply = response.choices[0].message.content
    if reply.startswith("get_temperature:"):
        arg = reply.split(":")[1].strip()
        temperature = get_temperature(arg)
        prompt = f"""
        You are a helpful assistant. Answer the user's question in a friendly way.

        Here is the user's question:
        <user-question>
        {user_input}
        </user-question>
        You requested to use the get_temperature tool for the city "{arg}".
        Here is the result of using that tool:
        The current temperature in {arg} is {temperature} degrees Celsius.
        """
        response = cliente.chat.completions.create(
            model="gpt-4o",
            input=prompt
        )
    print(f"Assistant: {reply}")

if __name__ == "__main__":
    main()