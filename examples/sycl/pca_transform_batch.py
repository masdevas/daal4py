#*******************************************************************************
# Copyright 2014-2020 Intel Corporation
# All Rights Reserved.
#
# This software is licensed under the Apache License, Version 2.0 (the
# "License"), the following terms apply:
#
# You may not use this file except in compliance with the License.  You may
# obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#*******************************************************************************

# daal4py PCA example for shared memory systems

import daal4py as d4p
import numpy as np
import os
from daal4py.oneapi import sycl_buffer

# let's try to use pandas' fast csv reader
try:
    import pandas
    read_csv = lambda f, c, t=np.float64: pandas.read_csv(f, usecols=c, delimiter=',', header=None, dtype=t)
except:
    # fall back to numpy loadtxt
    read_csv = lambda f, c, t=np.float64: np.loadtxt(f, usecols=c, delimiter=',', ndmin=2)

try:
    from dpctx import device_context, device_type
    with device_context(device_type.gpu, 0):
        gpu_available=True
except:
    try:
        from daal4py.oneapi import sycl_context
        with sycl_context('gpu'):
            gpu_available=True
    except:
        gpu_available=False

# Commone code for both CPU and GPU computations
def compute(data, nComponents):
    # configure a PCA object and perform PCA
    pca_algo = d4p.pca(isDeterministic=True, fptype='float', resultsToCompute="mean|variance|eigenvalue")
    pca_res = pca_algo.compute(data)
    # Apply transform with whitening because means and eigenvalues are provided
    pcatrans_algo = d4p.pca_transform(fptype='float', nComponents=nComponents)
    return pcatrans_algo.compute(data, pca_res.eigenvectors, pca_res.dataForTransform)


# At this moment with sycl we are working only with numpy arrays
def to_numpy(data):
    try:
        from pandas import DataFrame
        if isinstance(data, DataFrame):
            return np.ascontiguousarray(data.values)
    except ImportError:
        pass
    try:
        from scipy.sparse import csr_matrix
        if isinstance(data, csr_matrix):
            return data.toarray()
    except ImportError:
        pass
    return data


def main(readcsv=read_csv, method='svdDense'):
    dataFileName = os.path.join('..', 'data', 'batch', 'pca_transform.csv')
    nComponents = 2

    # read data
    data = readcsv(dataFileName, range(3), t=np.float32)

    # Using of the classic way (computations on CPU)
    result_classic = compute(data, nComponents)

    data = to_numpy(data)

    try:
        from dpctx import device_context, device_type
        gpu_context = lambda: device_context(device_type.gpu, 0)
        cpu_context = lambda: device_context(device_type.cpu, 0)
    except:
        from daal4py.oneapi import sycl_context
        gpu_context = lambda: sycl_context('gpu')
        cpu_context = lambda: sycl_context('cpu')

    # It is possible to specify to make the computations on GPU
    if gpu_available:
        with gpu_context():
            sycl_data = sycl_buffer(data)
            result_gpu = compute(sycl_data, nComponents)
        assert np.allclose(result_classic.transformedData, result_gpu.transformedData)

    # It is possible to specify to make the computations on CPU
    with cpu_context():
        sycl_data = sycl_buffer(data)
        result_cpu = compute(sycl_data, nComponents)

    # pca_transform_result objects provides transformedData
    assert np.allclose(result_classic.transformedData, result_cpu.transformedData)

    return (result_classic)


if __name__ == "__main__":
    pcatrans_res = main()
    # print results of tranform
    print(pcatrans_res)
    print('All looks good!')
