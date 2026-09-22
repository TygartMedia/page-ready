# Official Playwright Python image — browsers preinstalled
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PAGE_READY_ACCEPT_PAID=0 \
    PORT=8080 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY host ./host

RUN pip install -U pip \
 && pip install -e ".[host]"

EXPOSE 8080
CMD ["uvicorn", "host.app:app", "--host", "0.0.0.0", "--port", "8080"]
