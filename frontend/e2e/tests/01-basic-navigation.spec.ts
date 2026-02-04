import { test, expect } from '@playwright/test';

/**
 * Tests de navigation de base
 * Vérifie que l'application charge correctement et que la navigation fonctionne
 */

test.describe('Navigation de base', () => {
  test('devrait charger la page d\'accueil', async ({ page }) => {
    await page.goto('/');

    // Vérifier que la page charge
    await expect(page).toHaveTitle(/Supply Chain/i);
  });

  test('devrait afficher la page de login', async ({ page }) => {
    await page.goto('/login');

    // Vérifier les éléments de login
    await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/mot de passe/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /se connecter/i })).toBeVisible();
  });

  test('devrait afficher la page d\'inscription', async ({ page }) => {
    await page.goto('/register');

    // Vérifier les éléments d'inscription
    await expect(page.getByRole('heading', { name: /inscription/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /s'inscrire/i })).toBeVisible();
  });

  test('devrait rediriger vers login si non authentifié', async ({ page }) => {
    await page.goto('/chat');

    // Devrait être redirigé vers login
    await expect(page).toHaveURL(/\/login/);
  });
});
