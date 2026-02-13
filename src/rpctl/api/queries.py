"""GraphQL query strings for RunPod API."""

GPU_TYPES_LIST = """
query GpuTypes {
  gpuTypes {
    id
    displayName
    manufacturer
    memoryInGb
    cudaCores
    secureCloud
    communityCloud
    securePrice
    communityPrice
    secureSpotPrice
    communitySpotPrice
    maxGpuCount
    maxGpuCountSecureCloud
    maxGpuCountCommunityCloud
    lowestPrice(input: {gpuCount: 1}) {
      minimumBidPrice
      uninterruptablePrice
      stockStatus
      rentedCount
      totalCount
      rentalPercentage
      maxUnreservedGpuCount
      availableGpuCounts
    }
  }
}
"""

GPU_TYPE_AVAILABILITY = """
query GpuTypeAvailability($gpuTypeId: String!, $gpuCount: Int!, $secureCloud: Boolean) {
  gpuTypes(input: {id: $gpuTypeId}) {
    id
    displayName
    memoryInGb
    securePrice
    communityPrice
    secureSpotPrice
    communitySpotPrice
    lowestPrice(input: {gpuCount: $gpuCount, secureCloud: $secureCloud}) {
      minimumBidPrice
      uninterruptablePrice
      stockStatus
      rentedCount
      totalCount
      rentalPercentage
      maxUnreservedGpuCount
      availableGpuCounts
      countryCode
    }
  }
}
"""

DATACENTER_AVAILABILITY = """
query DatacenterAvailability {
  myself {
    datacenters {
      id
      name
      location
      region
      listed
      storageSupport
      gpuAvailability(input: {gpuCount: 1}) {
        gpuTypeId
        gpuTypeDisplayName
        available
        stockStatus
      }
    }
  }
}
"""

CPU_TYPES_LIST = """
query CpuTypes {
  cpuTypes {
    id
    displayName
    manufacturer
    cores
    threadsPerCore
    groupId
  }
}
"""
