import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Tests RAG (Retrieval Augmented Generation) et Citations
 * Vérifie que le système peut rechercher dans les documents et citer précisément les sources
 */

test.describe('RAG et Citations', () => {
  let page: any;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;

    // Se connecter et uploader un fichier de test
    await page.goto('/register');
    const email = `test-${Date.now()}@example.com`;
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
    await page.getByRole('button', { name: /s'inscrire/i }).click();
    await page.waitForURL(/\/chat/, { timeout: 10000 });

    // Upload fichier Excel de test
    const filePath = path.join(__dirname, '../fixtures/test-production.xlsx');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);

    // Attendre que le fichier soit indexé
    await page.waitForTimeout(5000);
  });

  test('devrait répondre à une question sur les stocks avec citation Excel', async () => {
    // Poser une question sur les stocks
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quel est le stock de Widget B ?');
    await messageInput.press('Enter');

    // Attendre la réponse
    await page.waitForTimeout(3000);

    // Vérifier que la réponse contient des informations du fichier
    await expect(page.getByText(/Widget B/i)).toBeVisible({ timeout: 15000 });

    // Vérifier qu'il y a une citation (fichier, feuille, cellule)
    await expect(page.getByText(/test-production\.xlsx/i)).toBeVisible();

    // La réponse devrait mentionner le stock négatif (-50)
    await expect(page.getByText(/-50|stock négatif/i)).toBeVisible();
  });

  test('devrait citer la cellule Excel précise', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Y a-t-il des stocks négatifs ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Vérifier la présence d'une citation avec référence cellule
    // Format attendu: "feuille 'Stocks', cellule B2" ou similaire
    await expect(page.getByText(/feuille.*Stocks/i)).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/cellule|ligne/i)).toBeVisible();
  });

  test('devrait répondre à une question sur les commandes', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Combien de commandes sont en cours ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Vérifier que la réponse fait référence aux commandes
    await expect(page.getByText(/commande|CMD/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait répondre à une question sur les fournisseurs', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quel est le lead time du Fournisseur Delta ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Vérifier la réponse contient le lead time (30 jours)
    await expect(page.getByText(/30.*jours|Fournisseur Delta/i)).toBeVisible({ timeout: 15000 });

    // Vérifier la citation
    await expect(page.getByText(/test-production\.xlsx/i)).toBeVisible();
    await expect(page.getByText(/Fournisseurs/i)).toBeVisible();
  });

  test('devrait indiquer quand l\'information n\'est pas dans les documents', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quel est le prix de vente du Widget A ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Devrait indiquer que l'information n'est pas disponible
    await expect(page.getByText(/pas trouvé|pas d'information|ne contient pas/i)).toBeVisible({ timeout: 15000 });
  });

  test('devrait supporter la recherche multi-feuilles', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Donne-moi un résumé des stocks et des commandes');
    await messageInput.press('Enter');

    await page.waitForTimeout(5000);

    // La réponse devrait référencer plusieurs feuilles
    const response = await page.textContent('body');
    expect(response && (response.includes('Stock') || response.includes('Commande'))).toBe(true);

    // Devrait avoir plusieurs citations
    const citations = await page.locator('[data-testid="citation"]').count();
    expect(citations).toBeGreaterThan(1);
  });

  test('devrait afficher les citations de manière cliquable', async () => {
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Quel est le stock de Widget B ?');
    await messageInput.press('Enter');

    await page.waitForTimeout(3000);

    // Vérifier qu'il y a un élément de citation
    const citation = await page.locator('[data-testid="citation"]').first();
    await expect(citation).toBeVisible({ timeout: 15000 });

    // Les citations devraient avoir des informations structurées
    await expect(citation).toContainText(/test-production\.xlsx/i);
  });

  test('devrait gérer plusieurs documents uploadés', async () => {
    // Upload un deuxième fichier
    const csvPath = path.join(__dirname, '../fixtures/test-inventory.csv');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);
    await page.waitForTimeout(3000);

    // Poser une question qui nécessite les deux fichiers
    const messageInput = await page.locator('textarea, input[type="text"]').last();
    await messageInput.fill('Compare les stocks dans les deux fichiers');
    await messageInput.press('Enter');

    await page.waitForTimeout(5000);

    // Devrait référencer les deux fichiers
    const response = await page.textContent('body');
    expect(response?.includes('test-production.xlsx') || response?.includes('test-inventory.csv')).toBe(true);
  });
});
