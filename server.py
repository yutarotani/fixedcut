from fixedcut_app import app

if __name__ == '__main__':
     # HTTPS 有効化（ローカルホスト限定）
    app.run(host="127.0.0.1", port=5000, debug=True,
            ssl_context=("cert.pem", "key.pem"))