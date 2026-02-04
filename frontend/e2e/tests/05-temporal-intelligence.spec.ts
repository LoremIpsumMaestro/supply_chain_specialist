import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Tests Intelligence Temporelle
 * Vérifie la détection automatique des dates, calcul des lead times, et analyse de tendances
 */

test.describe('Intelligence Temporelle', () => {
  let page: any;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;

    // Se connecter
    await page.goto('/register');
    const email = `test-${Date.now()}@example.com`;
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
    await page.getByRole('button', { name: /s'inscrire/i }).click();
    await page.waitForURL(/\/chat/, { timeout: 10000 });

    // Upload fichier avec dates
    const filePath = path.join(__dirname, '../fixtures/test-production.xlsx');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await page.waitForTimeout(5000);
  });

  test('devrait détecter automatiquement les colonnes de dates', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quelles sont les colonnes de dates dans le fichier ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Devrait identifier Date_Commande et Date_Livraison
    await expect(page.getByText(/Date.*Commande|Date.*Livraison/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait calculer les lead times automatiquement', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quel est le lead time moyen des commandes ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Devrait calculer et afficher le lead time
    await expect(page.getByText(/lead time|délai|jours/i)).toBeVisible({ timeout: 15000 });

    // Devrait mentionner un nombre de jours
    await expect(page.getByText(/\d+.*jours/i)).toBeVisible();
  });

  test('devrait identifier les commandes en retard', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Y a-t-il des commandes en retard ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Devrait identifier les retards
    await expect(page.getByText(/retard|en retard/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait comparer les dates avec la date actuelle', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quelles commandes doivent être livrées cette semaine ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Devrait utiliser la date système pour calculer
    const response = await page.textContent('body');
    expect(response).toBeTruthy();

    // La réponse devrait mentionner des dates ou "aucune"
    await expect(page.getByText(/date|cette semaine|aucune/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait calculer des statistiques temporelles', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Donne-moi les statistiques des lead times');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Devrait afficher min, max, moyenne
    await expect(page.getByText(/moyen|minimum|maximum|statistiques/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait identifier les outliers dans les lead times', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Y a-t-il des commandes avec des délais anormaux ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Le Fournisseur Delta a un lead time de 30 jours (outlier)
    await expect(page.getByText(/anormal|inhabituel|Fournisseur Delta|30 jours/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait supporter les questions sur la saisonnalité', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Y a-t-il une tendance saisonnière dans les commandes ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Devrait analyser ou indiquer qu'il n'y a pas assez de données
    await expect(page.getByText(/saisonnier|tendance|pas assez de données/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait inclure le contexte temporel dans les citations', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quand la commande CMD001 doit-elle être livrée ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // La réponse devrait inclure la date et la source
    await expect(page.getByText(/janvier|2024|date.*livraison/i)).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/test-production\.xlsx/i)).toBeVisible();
  });
});
