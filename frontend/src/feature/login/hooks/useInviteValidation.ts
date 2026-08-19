import { useEffect, useState } from 'react'
import { validateInviteToken } from '../api/registerApi'

type InviteValidationData = {
  email: string
  organization_name: string
}

type State =
  | { token: string | null; status: 'idle'; data: null; error: null }
  | { token: string | null; status: 'validating'; data: null; error: null }
  | { token: string | null; status: 'success'; data: InviteValidationData; error: null }
  | { token: string | null; status: 'error'; data: null; error: unknown }

export const useInviteValidation = (token?: string | null) => {
  const initialToken = token ?? null
  const [state, setState] = useState<State>(() => ({
    token: initialToken,
    status: initialToken ? 'validating' : 'idle',
    data: null,
    error: null,
  }))

  useEffect(() => {
    if (!token) return

    let cancelled = false

    validateInviteToken(token)
      .then((data) => {
        if (cancelled) return
        setState({ token, status: 'success', data, error: null })
      })
      .catch((err) => {
        if (cancelled) return
        setState({ token, status: 'error', data: null, error: err })
      })

    return () => {
      cancelled = true
    }
  }, [token])

  // Derive returned values ensuring we never expose stale data for a new token.
  if (!token) {
    return { data: null as InviteValidationData | null, error: null as string | null, isValidating: false }
  }

  if (state.token !== token) {
    // We have a new token but state belongs to an older token: indicate validating.
    return { data: null as InviteValidationData | null, error: null as string | null, isValidating: true }
  }

  if (state.status === 'validating') {
    return { data: null as InviteValidationData | null, error: null as string | null, isValidating: true }
  }

  if (state.status === 'success') {
    return { data: state.data, error: null as string | null, isValidating: false }
  }

  // error
  return { data: null as InviteValidationData | null, error: state.error, isValidating: false }
}
