#!/usr/bin/env bash
set +e
methods-audit check --paper data/sample/bad-cell-line.xml
exit $?
