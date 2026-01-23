'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/authStore'
import { AlertCircle } from 'lucide-react'

export default function RegisterPage() {
  const router = useRouter()
  const { register, isLoading, error, clearError } = useAuthStore()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  })

  const [validationError, setValidationError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setValidationError(null)

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setValidationError('Les mots de passe ne correspondent pas')
      return
    }

    // Validate password length
    if (formData.password.length < 8) {
      setValidationError(
        'Le mot de passe doit contenir au moins 8 caractères'
      )
      return
    }

    try {
      await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || undefined,
      })
      router.push('/chat')
    } catch (err) {
      // Error is handled by the store
      console.error('Registration failed:', err)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  const currentError = validationError || error

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Supply Chain AI Assistant
          </h1>
          <p className="mt-2 text-sm text-gray-600">Créez votre compte</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="mt-1"
                placeholder="votre.email@exemple.com"
              />
            </div>

            <div>
              <label
                htmlFor="full_name"
                className="block text-sm font-medium text-gray-700"
              >
                Nom complet (optionnel)
              </label>
              <Input
                id="full_name"
                name="full_name"
                type="text"
                autoComplete="name"
                value={formData.full_name}
                onChange={handleChange}
                className="mt-1"
                placeholder="Votre nom"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Mot de passe
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={handleChange}
                className="mt-1"
                placeholder="••••••••"
              />
              <p className="mt-1 text-xs text-gray-500">
                Minimum 8 caractères
              </p>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700"
              >
                Confirmer le mot de passe
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                className="mt-1"
                placeholder="••••••••"
              />
            </div>
          </div>

          {currentError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{currentError}</p>
            </div>
          )}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Création du compte...' : 'Créer mon compte'}
          </Button>

          <div className="text-center text-sm">
            <span className="text-gray-600">Déjà un compte ? </span>
            <Link
              href="/login"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              Se connecter
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
