#!/usr/bin/env bash
set +e
methods-audit score --paper data/sample/no-guide.xml --summary
exit $?
