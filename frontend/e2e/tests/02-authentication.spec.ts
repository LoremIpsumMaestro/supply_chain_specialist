import { test, expect } from '@playwright/test';

/**
 * Tests d'authentification
 * Vérifie l'inscription, la connexion, et la déconnexion
 */

test.describe('Authentification', () => {
  const testUser = {
    email: `test-${Date.now()}@example.com`,
    password: 'TestPassword123!',
  };

  test('devrait permettre l\'inscription d\'un nouvel utilisateur', async ({ page }) => {
    await page.goto('/register');

    // Remplir le formulaire d'inscription
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/mot de passe/i).first().fill(testUser.password);

    // Soumettre le formulaire
    await page.getByRole('button', { name: /s'inscrire/i }).click();

    // Attendre la redirection ou le message de succès
    await page.waitForURL(/\/(chat|login)/, { timeout: 10000 });
  });

  test('devrait permettre la connexion avec les bons identifiants', async ({ page }) => {
    // D'abord s'inscrire
    await page.goto('/register');
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/mot de passe/i).first().fill(testUser.password);
    await page.getByRole('button', { name: /s'inscrire/i }).click();
    await page.waitForTimeout(1000);

    // Ensuite se connecter
    await page.goto('/login');
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/mot de passe/i).fill(testUser.password);
    await page.getByRole('button', { name: /se connecter/i }).click();

    // Vérifier la redirection vers la page chat
    await expect(page).toHaveURL(/\/chat/, { timeout: 10000 });
  });

  test('devrait afficher une erreur avec de mauvais identifiants', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.getByLabel(/mot de passe/i).fill('wrongpassword');
    await page.getByRole('button', { name: /se connecter/i }).click();

    // Attendre un message d'erreur
    await expect(page.getByText(/erreur|invalide|incorrect/i)).toBeVisible({ timeout: 5000 });
  });
});
