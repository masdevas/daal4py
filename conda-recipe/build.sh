#!/bin/bash

DAAL4PY_VERSION=$PKG_VERSION CNCROOT=${PREFIX} TBBROOT=${PREFIX} DAALROOT=${PREFIX} ${PYTHON} setup.py install