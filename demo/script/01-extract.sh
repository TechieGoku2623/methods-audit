#!/usr/bin/env bash
set +e
methods-audit extract --paper data/sample/complete.xml --summary
exit $?
