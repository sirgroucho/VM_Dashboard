# Marx-Tec VM Dashboard

A lightweight, self-hosted Flask-based control dashboard for managing a home Minecraft server, users, and mod synchronization — securely routed through the cloud.

## 🚀 Project Overview

This project allows you to:

- Create and manage user accounts with role-based access (`admin`, `user`, etc.)
- Pair your Minecraft server with a cloud control dashboard
- Remotely monitor Minecraft server events (joins, crashes, restarts, etc.)
- Securely handle secrets and authentication (e.g., hashed passwords, role control)
- Route dashboard traffic through reverse proxy or Tailscale tunnel to reach your homelab
- Keep mod files/configs in sync between cloud and home servers via Git or file upload

## 🔒 Security Features

- Environment secrets are never tracked by Git
- Passwords stored using secure hashing (`werkzeug.security`)
- `.gitignore` excludes all secret files, API keys, and compiled Python
- Modular blueprint architecture keeps code clean and scalable

## 📁 Folder Structure

```

marx-tec-landing-page/
├── app.py                 # Entry point for Flask app
├── routes/                # Flask Blueprints (auth, minecraft)
├── static/                # Frontend scripts and styles
├── templates/             # HTML pages for Flask
├── utils/                 # Helpers, decorators
├── secrets/               # Local-only secrets (env, users.json) \[gitignored]
└── .gitignore             # Keeps secrets and junk out of version control

````

## 🛠️ Getting Started

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
````

2. **Set up secrets**

   * Create a `.env` file inside the `secrets/` folder:

     ```
     SECRET_KEY=your-very-secret-key
     ```
   * Create `secrets/users.json` to store users (auto-generated on user creation)

3. **Run the app**

   ```bash
   python app.py
   ```

4. **Visit the dashboard**

   ```
   http://localhost:5000/
   ```

## 👥 User Roles

* `admin`: Can create users, view logs, manage Minecraft config
* `user`: Limited to viewing dashboard

## ✅ Todo

* [ ] Add real-time websocket updates from Minecraft server
* [ ] Add mod upload + Git sync UI
* [ ] Deploy to Fly.io or Oracle Cloud (backend only)
* [ ] Add unit tests and CI

## 🧠 Technologies Used

* Flask (Python 3)
* HTML/CSS/JS frontend
* Werkzeug (for password hashing)
* dotenv for secret config
* Git for mod/config syncing

---

## 📜 License

MIT — do whatever you want, just don't expose the secrets 😎

---

## 🤝 Contributing

Right now this is personal-use only, but feel free to fork or adapt it. If you want help integrating Docker, Nginx, or auto-deploying, open an issue or hit me up.

```
