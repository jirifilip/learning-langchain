import marimo

__generated_with = "0.22.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from langchain.chat_models import init_chat_model

    return (init_chat_model,)


@app.cell
def _(init_chat_model):
    llm = init_chat_model("gpt-4o-mini")
    return (llm,)


@app.cell
def _():
    question = "The highest mountain on Venus?"
    return (question,)


@app.cell
def _(llm, question):
    llm.invoke(question)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
