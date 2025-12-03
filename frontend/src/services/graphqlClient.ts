import api from './api'

export interface GraphQLError {
  message: string
}

interface GraphQLResponse<T> {
  data?: T
  errors?: GraphQLError[]
}

export async function graphqlRequest<T = unknown, V extends Record<string, any> = Record<string, any>>(
  query: string,
  variables?: V
): Promise<T> {
  const response = await api.post('/graphql', {
    query,
    variables
  })

  const payload: GraphQLResponse<T> = response.data
  if (!payload) {
    throw new Error('GraphQL 服务未返回数据')
  }

  if (payload.errors && payload.errors.length > 0) {
    const message = payload.errors.map(err => err.message).join(' | ') || 'GraphQL 请求失败'
    throw new Error(message)
  }

  if (!payload.data) {
    throw new Error('GraphQL 响应缺少 data 字段')
  }

  return payload.data
}

export default {
  request: graphqlRequest
}

