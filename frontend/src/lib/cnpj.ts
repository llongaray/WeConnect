/** Remove caracteres não numéricos do CNPJ. */
export function normalizeCnpj(value: string): string {
  return value.replace(/\D/g, '')
}

/** Formata CNPJ enquanto o usuário digita. */
export function formatCnpjInput(value: string): string {
  const digits = normalizeCnpj(value).slice(0, 14)

  if (digits.length <= 2) return digits
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`
  if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`
  if (digits.length <= 12) {
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`
  }
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`
}

export function isValidCnpjLength(value: string): boolean {
  return normalizeCnpj(value).length === 14
}
