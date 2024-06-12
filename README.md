# User service

Simple user service with two endpoints:

1. `/api/users` with a `GET` to retrieve a list of users as a JSON, i.e:

        {"users":[{"name":"Arthur","email":"arthur@example.com"}]}

2. `/api/users` with a `POST` to create a user by providing a JSON in the body
    with:
    - `name` as a string, up to 256 characters,
    - `email` as a string and valid email, up to 256 characters.

    If the requirements are not meet the service with return an 422 error.

To use those endpoints you need to be authenticated with a Bearer token that
is a JWT token using `HS256` and the configured key, with a property `roles`
that is an array. To create a user that array must contain at least `admin`.

The authorization is deletegated to [OPA](https://www.openpolicyagent.org/).

The users are stored in [MongoDB](https://www.mongodb.com/), but are capped to
10000 since we return them in one request as JSON. The use-case need to refined,
with either options to batch or other options more suitable to larger
collections.

## Deployment

You can deploy the service for local testing on either
[minikube](https://minikube.sigs.k8s.io/docs/) or  Docker Desktop. This can be
done with the help of an (Helm)[https://helm.sh/] chart.

If you use minikube, first start it:

    minikube start

Please be aware that the provided chart is only intended for local use only. It
will take care of the dependencies, such as MongoDB and OPA, however you
definitely do not want to run MongoDB like this and in a production you would
rather rely on an external service provided through an operator to you. In a
similar way, the OPA server would probably serve more policies.

Install the chart (you need to provide a key for `USER_SERVICE_KEY`):

    helm install your-name charts/userservice --set key=$(openssl rand --hex 32)

You can verify that everything is running:

    kubectl get all -l app.kubernetes.io/instance=your-name

If you use minikube, run tunnel in a terminal to be able to access the
application:

    minikube tunnel

There is a convenience script to obtain a token.

You can list the users:

    MY_TOKEN=$(kubectl exec service/your-name-userservice -- /usr/local/bin/new-user-service-token)
    curl -H "Authorization: Bearer $MY_TOKEN" http://localhost:8000/api/users

You can add a user:

    MY_TOKEN=$(kubectl exec service/your-name-userservice -- /usr/local/bin/new-user-service-token admin)
    curl -H "Authorization: Bearer $MY_TOKEN" -H 'Content-Type: application/json' -X POST -d '{"name": "Arthur", "email": "arthur@example.com"}' http://localhost:8000/api/users

Alternatively you can use the docs to test the service at http://localhost:8000.

Cleanup with:

    helm uninstall your-name

If you use minikube:

    minikube stop

## Configuration

The following configuration variables are available:

- `USER_SERVICE_KEY`: JWT key used to authenticate to the service.
- `USER_SERVICE_ISSUER`: Issuer expected in the JWT key used to authenticate.
- `USER_SERVICE_LOG`: Custom logging configuration (a default one is provided).
- `USER_SERVICE_DATABASE`: URL to the a MongoDB database to store the users.
- `USER_SERVICE_SIZE`: Number of allowed users.
- `AUTHORIZATION_ENDPOINT`: URL to the OPA server.
- `AUTHORIZATION_POLICY`: Policy to use on the OPA server (default to userservice).

## Development

There is a dev container that can be used with vscode. It will take care of
starting an [OPA](https://www.openpolicyagent.org/) server in the background
to server the policies and a [MongoDB](https://www.mongodb.com/) server.
[Hatch](https://hatch.pypa.io/latest/) is used as a packaging tool, to run
test and code analysis.

### Testing

There is an helper script to generate a token with the configure key. First
start the service in a terminal:

    hatch run user-service

You can retrieve the list of users:

    MY_TOKEN=$(hatch run new-user-service-token)
    curl -H "Authorization: Bearer $MY_TOKEN" http://localhost:8000/api/users

You can add a user:

    MY_TOKEN=$(hatch run new-user-service-token admin)
    curl -H "Authorization: Bearer $MY_TOKEN" -H 'Content-Type: application/json' -X POST -d '{"name": "Arthur", "email": "arthur@example.com"}' http://localhost:8000/api/users

Alternatively you can use your browser and test it http://localhost:8000/docs.
