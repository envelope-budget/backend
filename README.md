# EnvelopeBudget 3.0

Welcome to the third incarnation of EnvelopeBudget (previously Inzolo)!

This version has been designed to be open source so that all the people who have reached out to me wanting to help can do so now and add whatever feature they want!

## Developer Setup

If you are running MacOS, simply run `./local_setup.sh`. It should install everything you need to run the development environment locally using docker-compose.

This will generate a placeholder `.env` file. Edit this file to the settings you would like.

To run the dev server, simply run `./run`.

### Tech Stack

The main application is built with [Django](https://www.djangoproject.com/), a high-level Python web framework that encourages rapid development and clean, pragmatic design.

For the API, we utilize [Django Ninja](https://django-ninja.dev/), a framework for building APIs with Django and Python 3.6+ type hints. It's similar to FastAPI but seamlessly integrates with Django, offering fast performance and automatic API documentation.

Our front-end stack consists of:

- [Alpine.js](https://alpinejs.dev/): A rugged, minimal framework for composing JavaScript behavior in your markup.
- [HTMX](https://htmx.org/): A powerful tool that allows you to access AJAX, CSS Transitions, WebSockets and Server Sent Events directly in HTML, using attributes.
- [Tailwind CSS](https://tailwindcss.com/): A utility-first CSS framework for rapidly building custom user interfaces.
- [Flowbite](https://flowbite.com/): A set of open-source UI components and templates built on top of Tailwind CSS.

This combination allows for a modern, responsive, and interactive user interface while maintaining simplicity and ease of development.

For database management, we use:

- [SQLite](https://www.sqlite.org/): A C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine. SQLite is used for development and self-hosted instances, providing a lightweight and easy-to-setup database solution.

### Keeping packages up to date

Use [pip-review](https://pypi.org/project/pip-review/) and [node-check-updates (ncu)](https://www.npmjs.com/package/node-check-updates) to keep your packages up to date regularly.

### Publishing to Docker Hub

To publish the EnvelopeBudget image to Docker Hub, execute the `./publish.sh` script.

Below is an example Docker Compose configuration for deploying EnvelopeBudget on your own server:

```yaml
services:
  budget:
    container_name: envelopebudget
    image: xhenxhe/envelopebudget:latest
    ports:
      - "8777:80"
      - "8778:8000"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=America/Denver
      - DEBUG=0
      - SECRET_KEY=YourSecretKey
      - DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.1,budget.example.com
      - CSRF_COOKIE_DOMAIN=192.168.1.1
      - SQLITE_DB_PATH=/app/data/db.sqlite3
      - DJANGO_SUPERUSER_EMAIL=<yourname@example.com>
      - DJANGO_SUPERUSER_PASSWORD=SuperSecretPassword
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Ensure to replace the placeholder values with your specific configuration details before deployment.
