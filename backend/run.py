from app import create_app

# ============FOR PRODUCTION--------------#

app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )

# ============FOR LOCAL DEVELOPMENT----------------#

# if __name__ == "__main__":
#     app.run(
#         debug=True,
#         port=5000
#     )