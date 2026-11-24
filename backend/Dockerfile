FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /bin/uv
WORKDIR ${LAMBDA_TASK_ROOT}

COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt \
    && uv pip install --no-cache --target . -r requirements.txt

COPY common common
COPY modules modules
COPY data data

# Both Lambdas use this image; the follow-up worker overrides the command with modules.followUpWorker.main.handler.
CMD ["modules.appApi.main.handler"]
