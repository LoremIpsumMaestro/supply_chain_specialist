import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'

export async function GET() {
  try {
    // Read the SVG icon
    const iconPath = path.join(process.cwd(), 'app', 'icon.svg')
    const iconContent = await fs.readFile(iconPath, 'utf-8')

    // Return it with appropriate headers
    return new NextResponse(iconContent, {
      headers: {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    })
  } catch (error) {
    return new NextResponse('Not Found', { status: 404 })
  }
}
