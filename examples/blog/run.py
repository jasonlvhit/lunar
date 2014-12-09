from blog import app

if __name__ == '__main__':
    print(app._router.rules)
    app.run(DEBUG=True)