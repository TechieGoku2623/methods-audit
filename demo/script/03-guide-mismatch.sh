#!/usr/bin/env bash
set +e
methods-audit check --paper data/sample/guide-mismatch.xml
exit $?
