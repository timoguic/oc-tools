#!/bin/bash

DOCKER_COMPOSE="/usr/local/bin/docker-compose"
BASE_DIR=$(readlink -f $(dirname "$0"))
COMPOSE_FILE="${BASE_DIR}/docker-compose.yml"
CUR_MONTH=$(date +%-m)
CUR_DIR="${BASE_DIR}/html"

CONTAINER="report"
RUN_DOCKER="$DOCKER_COMPOSE -f $COMPOSE_FILE run --rm $CONTAINER"

# Run the container
$RUN_DOCKER > "${CUR_DIR}/report-${CUR_MONTH}.html"

rm -f ${CUR_DIR}/index.html
ln -s report-${CUR_MONTH}.html ${CUR_DIR}/index.html

PREV_LINK="${CUR_DIR}/prev.html"

if [[ "$CUR_MONTH" -eq 1 ]]; then
    PREV_MONTH_FILE="report-12.html"
else
    PREV_MONTH_FILE="report-$(( CUR_MONTH - 1)).html"
fi

rm -f ${PREV_LINK}
ln -s ${PREV_MONTH_FILE} ${PREV_LINK}
