import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Session } from '@supabase/supabase-js';

import { ApiClient } from './src/api/client';
import { supabase, supabaseConfigured } from './src/api/supabase';
import { AuthScreen } from './src/screens/AuthScreen';
import { BreedPanel } from './src/screens/BreedPanel';
import { DogForm } from './src/screens/DogForm';
import { DogList } from './src/screens/DogList';
import { HabitsPanel } from './src/screens/HabitsPanel';
import { ResultPanel } from './src/screens/ResultPanel';
import { UploadPanel } from './src/screens/UploadPanel';
import { AnalysisJob, AnalysisResult, Dog, HabitSummary } from './src/types';

type Mode = 'local' | 'supabase';

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [mode, setMode] = useState<Mode>(supabaseConfigured ? 'supabase' : 'local');
  const [dogs, setDogs] = useState<Dog[]>([]);
  const [selectedDog, setSelectedDog] = useState<Dog | null>(null);
  const [currentJob, setCurrentJob] = useState<AnalysisJob | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [habits, setHabits] = useState<HabitSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const ownerId = mode === 'supabase' && session?.user.id ? session.user.id : 'local-demo-user';
  const api = useMemo(() => new ApiClient(ownerId), [ownerId]);

  useEffect(() => {
    if (!supabaseConfigured) {
      return;
    }
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  const refreshDogs = useCallback(async () => {
    setLoading(true);
    try {
      const loadedDogs = await api.listDogs();
      setDogs(loadedDogs);
      setSelectedDog((current) => current ?? loadedDogs[0] ?? null);
    } catch (error) {
      Alert.alert('Could not load dogs', error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    if (mode === 'local' || session) {
      refreshDogs();
    }
  }, [mode, refreshDogs, session]);

  const refreshHabits = useCallback(
    async (dogId: string) => {
      try {
        setHabits(await api.getHabits(dogId));
      } catch {
        setHabits(null);
      }
    },
    [api],
  );

  useEffect(() => {
    if (selectedDog) {
      refreshHabits(selectedDog.id);
    }
  }, [refreshHabits, selectedDog]);

  if (mode === 'supabase' && supabaseConfigured && !session) {
    return <AuthScreen onUseLocal={() => setMode('local')} />;
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <View>
            <Text style={styles.eyebrow}>Dog Translator</Text>
            <Text style={styles.title}>Behavior interpreter</Text>
          </View>
          <TouchableOpacity
            style={styles.modeButton}
            onPress={() => {
              if (mode === 'supabase') {
                supabase.auth.signOut();
                setMode('local');
              } else if (supabaseConfigured) {
                setMode('supabase');
              }
            }}
          >
            <Text style={styles.modeButtonText}>{mode === 'local' ? 'Local' : 'Supabase'}</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.disclaimer}>
          This app estimates probable behavior from video, audio, context, and feedback. It is not a
          veterinary diagnosis or a literal language translation.
        </Text>

        {loading ? <ActivityIndicator color="#2563eb" /> : null}

        <DogForm
          onCreate={async (payload) => {
            const dog = await api.createDog(payload);
            setDogs((items) => [dog, ...items]);
            setSelectedDog(dog);
          }}
        />

        <DogList
          dogs={dogs}
          selectedDogId={selectedDog?.id}
          onSelect={(dog) => {
            setSelectedDog(dog);
            setCurrentJob(null);
            setResult(null);
          }}
        />

        {selectedDog ? (
          <>
            <BreedPanel
              api={api}
              dog={selectedDog}
              onDogUpdated={(dog) => {
                setSelectedDog(dog);
                setDogs((items) => items.map((item) => (item.id === dog.id ? dog : item)));
              }}
            />
            <UploadPanel
              api={api}
              dog={selectedDog}
              ownerId={ownerId}
              onJobDone={(job, nextResult) => {
                setCurrentJob(job);
                setResult(nextResult);
                refreshHabits(selectedDog.id);
              }}
            />
            {currentJob ? <Text style={styles.job}>Latest job: {currentJob.status}</Text> : null}
            {result ? (
              <ResultPanel
                api={api}
                result={result}
                onFeedbackSaved={() => refreshHabits(selectedDog.id)}
              />
            ) : null}
            <HabitsPanel habits={habits} />
          </>
        ) : (
          <Text style={styles.empty}>Create a dog profile to start analyzing videos.</Text>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  container: {
    gap: 16,
    padding: 18,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  eyebrow: {
    color: '#2563eb',
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0,
    textTransform: 'uppercase',
  },
  title: {
    color: '#111827',
    fontSize: 30,
    fontWeight: '800',
    letterSpacing: 0,
  },
  disclaimer: {
    color: '#475569',
    fontSize: 14,
    lineHeight: 20,
  },
  modeButton: {
    backgroundColor: '#dbeafe',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  modeButtonText: {
    color: '#1d4ed8',
    fontWeight: '700',
  },
  job: {
    color: '#334155',
    fontSize: 14,
  },
  empty: {
    color: '#64748b',
    fontSize: 15,
  },
});
