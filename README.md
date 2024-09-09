# Take-home Assignments - External

This is a Flask application that connects to a MySQL database. It is Dockerized and can be built and run using Docker Compose. Additionally, it includes Kubernetes manifests for deployment.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [Docker](#docker)
  - [Docker Compose](#docker-compose)
  - [Kubernetes](#kubernetes)
- [CI/CD](#cicd)
- [License](#license)

## Features

- **Flask Application**: A simple Flask application for dns lookup.
- **Docker**: Containerized application with a Dockerfile.
- **Docker Compose**: Simplified local development setup.
- **Kubernetes**: Deployment manifests for Kubernetes.

## Prerequisites

- Docker: Ensure Docker is installed and running on your system.
- Docker Compose: Required for local development.
- Kubernetes: For deploying manifests.

## Setup

### Docker

1. **Build Docker Image**

   Build the Docker image with the following command:

   ```bash
   docker build -t my-flask-app:latest .
   ```

2. **Run Docker Container**

   Run the Docker container:

   ```bash
   docker run -d -p 3000:3000 --name my-flask-app \
    -e DB_URI='mysql://root:password@localhost/mydatabase' \
    my-flask-app:latest
   ```

   Access the application at `http://localhost:3000`.

### Docker Compose

1. **Configuration**

   The `docker-compose.yml` file is configured to build and run the Flask app and MySQL database. Make sure the file is in the root directory of your project.

   ```yaml
    version: '3.1'

    services:
        flask:
            build: 
                context: .
            networks:
                - app
            ports:
                - "3000:3000"
            environment:
                DB_URI: "${DB_URI}"
            depends_on:
                - db
            restart: always

        db:
            image: "mysql:8.0"
            ports:
                - "${DB_PORT}:3306"
            environment:
                MYSQL_ROOT_PASSWORD: "${DB_PASSWORD}"
                MYSQL_DATABASE: "${DB_DATABASE}"
                MYSQL_USER: "${DB_USERNAME}"
                MYSQL_PASSWORD: "${DB_PASSWORD}"
                MYSQL_ALLOW_EMPTY_PASSWORD: "yes"
            volumes:
                - "appdb:/var/lib/mysql"
            networks:
                - app
            restart: always

        phpmyadmin:
            depends_on:
                - db
            image: phpmyadmin/phpmyadmin
            restart: always
            ports:
                - "5005:80"
            environment:
                PMA_HOST: db
                MYSQL_ROOT_PASSWORD: "${DB_PASSWORD}"
            networks:
                - app

    volumes:
    appdb:

    networks:
    app:

   ```

2. **Run Docker Compose**

   Start the services using Docker Compose:

   ```bash
   docker-compose up -d --build
   ```

   Access the Flask application at `http://localhost:3000`.

### Kubernetes

1. **Kubernetes Manifests**

   The `k8s/manifests` directory contains Kubernetes manifests for deploying the application. Ensure that you have a Kubernetes cluster running and `kubectl` configured.

2. **Apply Kubernetes Manifests**

   Apply the manifests to your Kubernetes cluster:

   ```bash
   kubectl apply -f k8s/manifests/
   ```

   This will deploy the Flask application and MySQL database to your Kubernetes cluster.

## CI/CD

This repository includes a GitHub Actions workflow for continuous integration:

- **Linting**: Checks code quality using Pylint.
- **Testing**: Runs tests with pytest.
- **Build**: Builds and pushes Docker images.

Ensure you have the necessary secrets (`DOCKER_USERNAME` and `DOCKER_PASSWORD`) set up in your GitHub repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to customize this `README.md` further to suit your project's specific needs and details.