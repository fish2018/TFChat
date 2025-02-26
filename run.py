from apps import create_app
app = create_app("TencentAIChatBot")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1234, workers=1, auto_reload=True, debug=False)




