import { test, expect } from '@playwright/test';

/**
 * Tests Responsive Design
 * Vérifie que l'interface fonctionne correctement sur desktop, tablette, et mobile
 */

test.describe('Responsive Design', () => {
  test.describe('Desktop (1920x1080)', () => {
    test.use({ viewport: { width: 1920, height: 1080 } });

    test('devrait afficher l\'interface complète en desktop', async ({ page }) => {
      await page.goto('/login');

      // Vérifier les éléments principaux
      await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /se connecter/i })).toBeVisible();

      // Vérifier que le layout est horizontal
      const loginForm = await page.locator('form').first();
      const box = await loginForm.boundingBox();
      expect(box?.width).toBeGreaterThan(300);
    });

    test('devrait afficher la sidebar en desktop après connexion', async ({ page }) => {
      // Se connecter
      await page.goto('/register');
      const email = `test-${Date.now()}@example.com`;
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
      await page.getByRole('button', { name: /s'inscrire/i }).click();
      await page.waitForURL(/\/chat/, { timeout: 10000 });

      // Vérifier la sidebar (liste des conversations)
      await expect(page.getByText(/conversations|historique/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Tablette (768x1024)', () => {
    test.use({ viewport: { width: 768, height: 1024 } });

    test('devrait afficher l\'interface en mode tablette', async ({ page }) => {
      await page.goto('/login');

      // Les éléments doivent être visibles et accessibles
      await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /se connecter/i })).toBeVisible();
    });

    test('devrait avoir une sidebar collapsible en tablette', async ({ page }) => {
      await page.goto('/register');
      const email = `test-${Date.now()}@example.com`;
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
      await page.getByRole('button', { name: /s'inscrire/i }).click();
      await page.waitForURL(/\/chat/, { timeout: 10000 });

      // En tablette, la sidebar peut être cachée par défaut
      // Chercher un bouton menu ou hamburger
      const menuButton = await page.locator('[aria-label*="menu"], [data-testid*="menu"], button[class*="menu"]').first();

      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500);

        // La sidebar devrait apparaître
        await expect(page.getByText(/conversations|historique/i)).toBeVisible({ timeout: 5000 });
      }
    });
  });

  test.describe('Mobile (375x667 - iPhone SE)', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('devrait afficher l\'interface en mode mobile', async ({ page }) => {
      await page.goto('/login');

      // Les éléments doivent être visibles et empilés verticalement
      await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /se connecter/i })).toBeVisible();

      // Les inputs doivent prendre toute la largeur
      const emailInput = await page.getByLabel(/email/i);
      const box = await emailInput.boundingBox();
      expect(box?.width).toBeGreaterThan(300);
    });

    test('devrait cacher la sidebar par défaut en mobile', async ({ page }) => {
      await page.goto('/register');
      const email = `test-${Date.now()}@example.com`;
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
      await page.getByRole('button', { name: /s'inscrire/i }).click();
      await page.waitForURL(/\/chat/, { timeout: 10000 });

      // En mobile, la sidebar devrait être cachée
      // Chercher un bouton menu
      const menuButton = await page.locator('[aria-label*="menu"], [data-testid*="menu"], button[class*="menu"]').first();
      await expect(menuButton).toBeVisible({ timeout: 5000 });
    });

    test('devrait permettre d\'ouvrir la sidebar en mobile', async ({ page }) => {
      await page.goto('/register');
      const email = `test-${Date.now()}@example.com`;
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
      await page.getByRole('button', { name: /s'inscrire/i }).click();
      await page.waitForURL(/\/chat/, { timeout: 10000 });

      // Cliquer sur le menu
      const menuButton = await page.locator('[aria-label*="menu"], [data-testid*="menu"], button[class*="menu"]').first();

      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500);

        // La sidebar devrait apparaître en overlay
        await expect(page.getByText(/conversations|historique|nouvelle conversation/i)).toBeVisible({ timeout: 5000 });
      }
    });

    test('devrait avoir des boutons tactiles suffisamment grands', async ({ page }) => {
      await page.goto('/login');

      // Les boutons doivent avoir une taille minimum (44x44px recommandé)
      const loginButton = await page.getByRole('button', { name: /se connecter/i });
      const box = await loginButton.boundingBox();

      expect(box?.height).toBeGreaterThanOrEqual(40);
      expect(box?.width).toBeGreaterThanOrEqual(100);
    });
  });

  test.describe('Tests de défilement', () => {
    test('devrait permettre le défilement de l\'historique des messages', async ({ page }) => {
      await page.goto('/register');
      const email = `test-${Date.now()}@example.com`;
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
      await page.getByRole('button', { name: /s'inscrire/i }).click();
      await page.waitForURL(/\/chat/, { timeout: 10000 });

      // Envoyer plusieurs messages pour tester le scroll
      const messageInput = await page.locator('textarea, input[type="text"]').last();

      for (let i = 0; i < 5; i++) {
        await messageInput.fill(`Message de test ${i + 1}`);
        await messageInput.press('Enter');
        await page.waitForTimeout(1000);
      }

      // Vérifier que tous les messages sont présents (même si pas tous visibles)
      for (let i = 0; i < 5; i++) {
        await expect(page.getByText(`Message de test ${i + 1}`)).toBeAttached();
      }

      // Vérifier que l'area de chat est scrollable
      const chatArea = await page.locator('[data-testid="chat-messages"], [class*="messages"], [class*="chat-area"]').first();
      const isScrollable = await chatArea.evaluate((el) => el.scrollHeight > el.clientHeight);
      expect(isScrollable).toBe(true);
    });
  });

  test.describe('Tests d\'orientation', () => {
    test('devrait fonctionner en mode paysage sur mobile', async ({ page }) => {
      await page.setViewportSize({ width: 667, height: 375 });
      await page.goto('/login');

      // Les éléments doivent rester accessibles
      await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
      await expect(page.getByLabel(/email/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /se connecter/i })).toBeVisible();
    });
  });
});
