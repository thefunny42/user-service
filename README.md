# User service

Simple user service with two endpoints:

1. `/api/users` with a `GET` to retrieve a list of users as a JSON, i.e:

    ```json
        {"users":[{"name":"Arthur","email":"arthur@example.com"}]}
    ```

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
done with the help of an [Helm](https://helm.sh/) chart.

If you use minikube, first start it:

```shell
minikube start --network-plugin=cni
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml
```

Install the chart:

```shell
helm repo add thefunny42 https://thefunny42.github.io/charts
helm install your-name thefunny42/userservice
```

Alternatively you can install it from a clone from this repository:

```shell
helm install your-name charts/userservice
```

You can verify that everything is running:

```shell
helm test your-name
kubectl get all -l app.kubernetes.io/instance=your-name
```

If you use minikube, run tunnel in a terminal to be able to access the
application:

```shell
minikube tunnel
```

There is a convenience script to obtain a token.

You can list the users:

```shell
MY_TOKEN=$(kubectl exec service/your-name-userservice -- /app/bin/new-user-service-token)
curl -H "Authorization: Bearer $MY_TOKEN" http://localhost:8000/api/users
```

You can add a user:

```shell
MY_TOKEN=$(kubectl exec service/your-name-userservice -- /app/bin/new-user-service-token admin)
curl -H "Authorization: Bearer $MY_TOKEN" -H 'Content-Type: application/json' -X POST -d '{"name": "Arthur", "email": "arthur@example.com"}' http://localhost:8000/api/users
```

Alternatively you can use the docs to test the service at http://localhost:8000.

Cleanup with:

```shell
helm uninstall your-name
```

If you use minikube:

```shell
minikube stop
```

## Configuration

The following configuration variables are available:

- `USER_SERVICE_KEY`: JWT key used to authenticate to the service.
- `USER_SERVICE_JWKS_URL`: URL to fetch JWKS to validate JWT token (instead of key).
- `USER_SERVICE_ISSUER`: Issuer expected in the JWT token used to authenticate.
- `USER_SERVICE_LOG_CONFIG`: Custom logging configuration (a default one is provided).
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

```shell
hatch run user-service
```

You can retrieve the list of users:

```shell
MY_TOKEN=$(hatch run new-user-service-token)
curl -H "Authorization: Bearer $MY_TOKEN" http://localhost:8000/api/users
```

You can add a user:

```shell
MY_TOKEN=$(hatch run new-user-service-token admin)
curl -H "Authorization: Bearer $MY_TOKEN" -H 'Content-Type: application/json' -X POST -d '{"name": "Arthur", "email": "arthur@example.com"}' http://localhost:8000/api/users
```

Alternatively you can use your browser and test it http://localhost:8000/docs.

### What else might be done

1. Configure authentication to interact with the OPA agent, currently that is
   not protected.

2. Configure authentication to MongoDB.

3. Use SSL certificates for the JWT tokens depending on the use-case.
