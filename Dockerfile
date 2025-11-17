# Local Weaviate for development (no auth)
FROM semitechnologies/weaviate:latest

ENV QUERY_DEFAULTS_LIMIT=25
ENV AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
ENV PERSISTENCE_DATA_PATH=/var/lib/weaviate
ENV DEFAULT_VECTORIZER_MODULE=none
ENV ENABLE_MODULES=none

EXPOSE 8080

CMD ["server"]