"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

interface TemporalMetadata {
  upload_date: string;
  detected_date_columns: string[];
  user_configured_columns?: string[] | null;
  time_range?: {
    earliest: string;
    latest: string;
  } | null;
  lead_time_stats?: {
    mean_days: number;
    median_days: number;
    max_days: number;
    min_days: number;
    outliers: number[];
  } | null;
}

interface TemporalMetadataResponse {
  file_id: string;
  filename: string;
  temporal_metadata: TemporalMetadata | null;
}

interface TemporalMetadataPanelProps {
  fileId: string;
  onUpdate?: () => void;
}

export function TemporalMetadataPanel({ fileId, onUpdate }: TemporalMetadataPanelProps) {
  const [metadata, setMetadata] = useState<TemporalMetadata | null>(null);
  const [selectedColumns, setSelectedColumns] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTemporalMetadata();
  }, [fileId]);

  const fetchTemporalMetadata = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get<TemporalMetadataResponse>(
        `/files/${fileId}/temporal-metadata`
      );

      const meta = response.temporal_metadata;
      setMetadata(meta);

      // Initialize selected columns with detected or user-configured columns
      if (meta) {
        const columns = meta.user_configured_columns || meta.detected_date_columns || [];
        setSelectedColumns(new Set(columns));
      }
    } catch (err: any) {
      console.error("Error fetching temporal metadata:", err);
      setError(err.message || "Erreur lors du chargement des métadonnées temporelles");
    } finally {
      setLoading(false);
    }
  };

  const handleColumnToggle = (column: string) => {
    const newSelected = new Set(selectedColumns);
    if (newSelected.has(column)) {
      newSelected.delete(column);
    } else {
      newSelected.add(column);
    }
    setSelectedColumns(newSelected);
  };

  const handleRecalculate = async () => {
    try {
      setUpdating(true);
      setError(null);

      await api.patch(`/files/${fileId}/temporal-config`, {
        date_columns: Array.from(selectedColumns),
      });

      // Refresh metadata after recalculation
      setTimeout(() => {
        fetchTemporalMetadata();
        onUpdate?.();
      }, 2000); // Wait 2s for reprocessing to start

    } catch (err: any) {
      console.error("Error updating temporal config:", err);
      setError(err.response?.data?.detail || "Erreur lors de la mise à jour");
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analyse Temporelle</CardTitle>
          <CardDescription>Chargement...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!metadata || !metadata.detected_date_columns || metadata.detected_date_columns.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Analyse Temporelle</CardTitle>
          <CardDescription>
            Aucune colonne temporelle détectée dans ce fichier.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const allColumns = metadata.user_configured_columns || metadata.detected_date_columns;
  const hasChanges = JSON.stringify(Array.from(selectedColumns).sort()) !==
                     JSON.stringify(allColumns.sort());

  return (
    <Card>
      <CardHeader>
        <CardTitle>Analyse Temporelle</CardTitle>
        <CardDescription>
          Configuration des colonnes de dates pour l'analyse temporelle
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Time Range */}
        {metadata.time_range && (
          <div className="p-3 bg-blue-50 rounded-md">
            <p className="text-sm font-medium text-blue-900">Période des données</p>
            <p className="text-sm text-blue-700">
              Du {new Date(metadata.time_range.earliest).toLocaleDateString('fr-FR')} au{' '}
              {new Date(metadata.time_range.latest).toLocaleDateString('fr-FR')}
            </p>
          </div>
        )}

        {/* Lead Time Stats */}
        {metadata.lead_time_stats && (
          <div className="p-3 bg-green-50 rounded-md">
            <p className="text-sm font-medium text-green-900">Statistiques Lead Time</p>
            <div className="grid grid-cols-2 gap-2 mt-2 text-sm text-green-700">
              <div>Moyenne: {metadata.lead_time_stats.mean_days.toFixed(1)} jours</div>
              <div>Médiane: {metadata.lead_time_stats.median_days.toFixed(1)} jours</div>
              <div>Min: {metadata.lead_time_stats.min_days.toFixed(0)} jours</div>
              <div>Max: {metadata.lead_time_stats.max_days.toFixed(0)} jours</div>
            </div>
            {metadata.lead_time_stats.outliers.length > 0 && (
              <p className="mt-2 text-sm text-orange-600">
                ⚠️ {metadata.lead_time_stats.outliers.length} valeur(s) aberrante(s) détectée(s)
              </p>
            )}
          </div>
        )}

        {/* Detected Columns */}
        <div>
          <Label className="text-base font-semibold">Colonnes Temporelles</Label>
          <p className="text-sm text-gray-600 mb-3">
            Sélectionnez les colonnes de dates à utiliser pour l'analyse
          </p>

          <div className="space-y-2">
            {metadata.detected_date_columns.map((column) => (
              <div key={column} className="flex items-center space-x-2">
                <Checkbox
                  id={column}
                  checked={selectedColumns.has(column)}
                  onCheckedChange={() => handleColumnToggle(column)}
                />
                <Label
                  htmlFor={column}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {column}
                </Label>
              </div>
            ))}
          </div>

          {metadata.user_configured_columns && (
            <p className="mt-2 text-xs text-blue-600">
              ℹ️ Configuration personnalisée active
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <Button
            onClick={handleRecalculate}
            disabled={!hasChanges || updating}
            variant={hasChanges ? "default" : "outline"}
          >
            {updating ? "Recalcul en cours..." : "Recalculer"}
          </Button>

          {hasChanges && (
            <p className="text-sm text-orange-600">
              Des modifications non enregistrées
            </p>
          )}
        </div>

        {/* Error display */}
        {error && (
          <div className="p-3 bg-red-50 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
