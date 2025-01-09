FROM langchain/langgraph-api:3.12



ADD requirements.txt /deps/__outer_studio/src/requirements.txt
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -c /api/constraints.txt -r /deps/__outer_studio/src/requirements.txt

ADD . /deps/__outer_studio/src
RUN set -ex && \
    for line in '[project]' \
                'name = "studio"' \
                'version = "0.1"' \
                '[tool.setuptools.package-data]' \
                '"*" = ["**/*"]'; do \
        echo "$line" >> /deps/__outer_studio/pyproject.toml; \
    done

RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -c /api/constraints.txt -e /deps/*

RUN python -m playwright install && playwright install-deps

ENV LANGSERVE_GRAPHS='{"rag_chatbot": "/deps/__outer_studio/src/develop.py:graph"}'

WORKDIR /deps/__outer_studio/src