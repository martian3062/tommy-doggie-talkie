import React, { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { ApiClient } from '../api/client';
import { AnalysisResult } from '../types';
import { Panel } from '../components/Panel';
import { PrimaryButton } from '../components/PrimaryButton';

type Props = {
  api: ApiClient;
  result: AnalysisResult;
  onFeedbackSaved: () => void;
};

export function ResultPanel({ api, result, onFeedbackSaved }: Props) {
  const [selectedLabel, setSelectedLabel] = useState(result.top_predictions[0]?.label ?? 'unknown');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  async function saveFeedback(isCorrect: boolean) {
    setSaving(true);
    try {
      await api.sendFeedback(result.job_id, selectedLabel, isCorrect, note || undefined);
      Alert.alert('Feedback saved', 'This correction will feed the personal dog profile.');
      onFeedbackSaved();
    } catch (error) {
      Alert.alert('Could not save feedback', error instanceof Error ? error.message : String(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Panel>
      <Text style={styles.heading}>Interpretation</Text>
      {result.top_predictions.map((prediction) => (
        <TouchableOpacity
          key={prediction.label}
          style={[styles.prediction, selectedLabel === prediction.label && styles.selected]}
          onPress={() => setSelectedLabel(prediction.label)}
        >
          <View style={styles.predictionHeader}>
            <Text style={styles.label}>{prediction.label}</Text>
            <Text style={styles.confidence}>{Math.round(prediction.confidence * 100)}%</Text>
          </View>
          {prediction.evidence.map((item) => (
            <Text key={item} style={styles.evidence}>
              {item}
            </Text>
          ))}
        </TouchableOpacity>
      ))}
      {result.uncertainty_reason ? <Text style={styles.warning}>{result.uncertainty_reason}</Text> : null}
      <TextInput
        placeholder="Correction note, e.g. actually wanted food"
        style={styles.input}
        value={note}
        onChangeText={setNote}
      />
      <View style={styles.buttons}>
        <PrimaryButton label="Correct" loading={saving} onPress={() => saveFeedback(true)} />
        <PrimaryButton label="Wrong" variant="secondary" loading={saving} onPress={() => saveFeedback(false)} />
      </View>
    </Panel>
  );
}

const styles = StyleSheet.create({
  heading: {
    color: '#111827',
    fontSize: 18,
    fontWeight: '800',
  },
  prediction: {
    backgroundColor: '#f8fafc',
    borderColor: '#e2e8f0',
    borderRadius: 8,
    borderWidth: 1,
    gap: 6,
    padding: 12,
  },
  selected: {
    borderColor: '#2563eb',
  },
  predictionHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  label: {
    color: '#111827',
    fontSize: 16,
    fontWeight: '800',
    textTransform: 'capitalize',
  },
  confidence: {
    color: '#1d4ed8',
    fontWeight: '800',
  },
  evidence: {
    color: '#475569',
    fontSize: 13,
  },
  warning: {
    backgroundColor: '#fef3c7',
    borderRadius: 8,
    color: '#92400e',
    padding: 10,
  },
  input: {
    backgroundColor: '#f8fafc',
    borderColor: '#cbd5e1',
    borderRadius: 8,
    borderWidth: 1,
    fontSize: 15,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  buttons: {
    flexDirection: 'row',
    gap: 10,
  },
});
