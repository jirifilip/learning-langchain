import marimo

__generated_with = "0.22.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    Hello world!
    """)
    return


@app.cell
def _():
    a = 1
    return (a,)


@app.cell
def _():
    b = 4
    return (b,)


@app.cell
def _(a, b, mo):
    mo.md(f"# result is {a + b}")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
