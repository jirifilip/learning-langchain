import marimo

__generated_with = "0.22.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from langchain.chat_models import init_chat_model
    from langchain.messages import HumanMessage

    return HumanMessage, init_chat_model


@app.cell
def _(init_chat_model):
    llm = init_chat_model("gpt-4o-mini")
    return (llm,)


@app.cell
def _(mo):
    get_chat_history, set_chat_history = mo.state([])
    return get_chat_history, set_chat_history


@app.cell
def _(HumanMessage, get_chat_history, llm, mo, set_chat_history):
    def _handle_send_message(*args):
        user_message = input_message.value.strip()
        updated_history = get_chat_history() + [HumanMessage(content=user_message)]
        set_chat_history(updated_history)

        response = llm.invoke(input=updated_history)
        set_chat_history(lambda history: history + [response])

    input_message = mo.ui.text(
        placeholder="Type a message...",
        full_width=True
    )
    send_message = mo.ui.button(
        label="Send",
        on_click=_handle_send_message
    )
    return input_message, send_message


@app.cell
def _(HumanMessage, get_chat_history, input_message, mo, send_message):
    history = [
        mo.md(("> " if type(message) is HumanMessage else "") + message.content) for message in get_chat_history()
    ]
    mo.vstack([
        *history,
        mo.hstack(
            [input_message, send_message],
            widths=[90, 10]
        )
    ])
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
