"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

// --- Types for cleaner access ---
interface WrappedData {
  steps_total: number;
  distance_total_km: number;
  flights_total: number;
  total_runs: number;
  longest_run_km: number;
  fastest_pace_min_per_km: number | null;
  run_distances: number[];
  resting_hr_avg: number;
  workout_hr_avg: number;
  workouts_count: number;
  highest_workout_bpm: number;
  avg_workout_bpm: number;
  avg_workout_time_min: number;
  avg_calories_per_workout: number;
  total_workout_calories: number;
  most_calories_burned_day: string;
  most_calories_burned_value: number;
  move_total: number;
  exercise_total: number;
  stand_total: number;
  steps_monthly: { [key: number]: number };
  workouts_monthly: { [key: number]: number };
  wrapped_year: number;

  // --- NEW SLEEP STATS ---
  total_net_sleep_hours: number;
  total_nights_with_data: number;
  avg_sleep_per_night: number;
  avg_bedtime: string;
  avg_waketime: string;

  longest_sleep_night: { duration_hours: number; date_woke: string };
  most_woken_night: { awakening_count: number; date_woke: string };
  shortest_sleep_night?: { duration_hours: number; date_woke: string };
}

export default function Home() {
  const [data, setData] = useState<WrappedData | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/wrapped")
      .then((res) => res.json())
      .then((json: WrappedData) => setData(json))
      .catch((error) => console.error("Failed to fetch wrapped data:", error));
  }, []);

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black text-white text-xl">
        Loading your Wrapped…
      </div>
    );
  }

  const totalRunDistance = (data.run_distances ?? [])
    .reduce((a: number, b: number) => a + b, 0)
    .toFixed(2);

  const fadeUp = {
    initial: { opacity: 0, y: 30 },
    whileInView: { opacity: 1, y: 0 },
    transition: { duration: 0.8 },
    viewport: { once: true as const },
  };

  return (
    <div className="snap-y snap-mandatory h-screen overflow-y-scroll w-full bg-black text-white">
      {/* HERO SECTION */}
      <section className="snap-start h-screen flex flex-col items-center justify-center text-center px-8 bg-gradient-to-b from-purple-900 to-black">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="text-7xl font-extrabold tracking-tight mb-6"
        >
          {data.wrapped_year} Health Wrapped
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="text-2xl text-zinc-300 max-w-2xl"
        >
          Statistical analysis of your health throughout the year.
        </motion.p>
      </section>

      {/* MOVEMENT */}
      <MovementIntro />

      <Slide>
        <StatBig
          value={data.steps_total.toLocaleString()}
          label="Total Steps"
          color="from-blue-500 to-purple-500"
        />
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-2xl text-zinc-300 max-w-2xl"
        >
          {getStepsMessage(data.steps_total)}
        </motion.p>
      </Slide>

      <Slide>
        <StatBig
          value={`${data.distance_total_km.toLocaleString()} km`}
          label="Distance Covered"
          color="from-amber-400 via-orange-500 to-pink-500"
        />
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-2xl text-zinc-300 max-w-2xl"
        >
          {getDistanceMessage(data.distance_total_km)}
        </motion.p>
      </Slide>

      <Slide>
        <StatBig
          value={data.flights_total.toLocaleString()}
          label="Flights Climbed"
          color="from-cyan-400 via-blue-500 to-indigo-500"
        />

        <motion.pre
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-lime-300 font-mono text-lg leading-tight whitespace-pre"
        >
          {` _ _|_ _|_|_ _|_|_|_ _|_|_|_|_`}
        </motion.pre>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-2xl text-zinc-300 max-w-2xl"
        >
          {getFlightsMessage(data.flights_total)}
        </motion.p>
      </Slide>

      <Slide>
        <motion.h3
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-4xl font-semibold text-zinc-100"
        >
          Steps per Month
        </motion.h3>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-lg text-zinc-400 max-w-xl"
        >
          Brother was ACTIVE during the summer!
        </motion.p>

        <MonthlyStepsChart steps={data.steps_monthly} />
      </Slide>

      {/* SLEEP */}
      <SleepIntro />

      <Slide>
        <StatBig
          value={`${Math.round(data.total_net_sleep_hours).toLocaleString()} hrs`}
          label="You slept this many hours"
          color="from-indigo-400 via-purple-500 to-pink-500"
        />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.2 }}
          className="flex flex-col items-center gap-3"
        >
          <span className="text-sm uppercase tracking-[0.4em] text-purple-200/80">
            Average Sleep Time
          </span>

          <div className="px-8 py-4 rounded-full border border-purple-400/40 bg-purple-500/10 text-3xl font-semibold text-white shadow-[0_0_40px_rgba(168,85,247,0.35)]">
            {Number(data.avg_sleep_per_night).toFixed(1)} hrs
          </div>
        </motion.div>
      </Slide>

      <Slide>
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
          <SleepCard
            label="Average Bedtime"
            value={data.avg_bedtime || "N/A"}
            note={getBedtimeMessage(data.avg_bedtime)}
          />
          <SleepCard
            label="Average Wake Time"
            value={data.avg_waketime || "N/A"}
            note={getWakeMessage(data.avg_waketime)}
          />
          <SleepCard
            label="Nights Recorded"
            value={`${data.total_nights_with_data ?? 0}`}
            note="Each dot is a story your pillow could tell."
          />
        </div>
      </Slide>

      <Slide>
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
          <SleepCard
            label="Most Woken Night"
            value={`${data.most_woken_night?.awakening_count ?? "N/A"} wake-ups`}
            note={getRestlessNightMessage(data.most_woken_night?.awakening_count)}
            footer={data.most_woken_night?.date_woke}
          />

          <SleepCard
            label="Longest Sleep"
            value={`${data.longest_sleep_night?.duration_hours ?? "N/A"} hrs`}
            note={getLongestSleepMessage(data.longest_sleep_night?.duration_hours)}
            footer={data.longest_sleep_night?.date_woke}
          />

          <SleepCard
            label="Shortest Sleep"
            value={`${data.shortest_sleep_night?.duration_hours ?? "N/A"} hrs`}
            note={getShortestSleepMessage(data.shortest_sleep_night?.duration_hours)}
            footer={data.shortest_sleep_night?.date_woke}
          />
        </div>
      </Slide>

      {/* RUNNING */}
      <RunningIntro />

      <Slide>
        <StatBig
          value={data.total_runs}
          label="Total Runs"
          color="from-green-400 via-emerald-500 to-cyan-500"
          size="text-7xl md:text-8xl"
        />
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-2xl text-zinc-300 max-w-2xl"
        >
          {getRunCountMessage(data.total_runs)}
        </motion.p>
      </Slide>

      <Slide>
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
          <RunCard
            label="Longest Run"
            value={`${data.longest_run_km} km`}
            note={getLongestRunMessage(data.longest_run_km)}
          />
          <RunCard
            label="Fastest Pace"
            value={`${data.fastest_pace_min_per_km} min/km`}
            note={getFastestPaceMessage(data.fastest_pace_min_per_km)}
          />
          <RunCard
            label="Distance in Runs"
            value={`${totalRunDistance} km`}
            note={getRunDistanceMessage(Number(totalRunDistance))}
          />
        </div>
      </Slide>

      {/* FITNESS */}
      <FitnessIntro />

      <Slide>
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
          <FitnessCard
            label="Exercise Minutes"
            value={`${data.exercise_total ?? 0} min`}
            note={getExerciseMinutesMessage(data.exercise_total ?? 0)}
          />
          <FitnessCard
            label="Calories Burned"
            value={`${data.total_workout_calories ?? 0} kcal`}
            note={getCaloriesBurnedMessage(data.total_workout_calories ?? 0)}
          />
          <FitnessCard
            label="Stand Hours"
            value={`${data.stand_total ?? 0} hrs`}
            note={getStandHoursMessage(data.stand_total ?? 0)}
          />
        </div>
      </Slide>

      <Slide>
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6">
          <FitnessCard
            label="Highest Workout BPM"
            value={`${data.highest_workout_bpm ?? 0} bpm`}
            note={getWorkoutBPMMessage(
              data.highest_workout_bpm ?? 0,
              "high"
            )}
            variant="alert"
          />

          <FitnessCard
            label="Average Workout BPM"
            value={`${data.avg_workout_bpm ?? 0} bpm`}
            note={getWorkoutBPMMessage(data.avg_workout_bpm ?? 0, "avg")}
            variant="alert"
          />
        </div>
      </Slide>

      <Slide>
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6">
          <FitnessCard
            label="Avg Workout Time"
            value={`${data.avg_workout_time_min ?? 0} min`}
            note={getAvgWorkoutTimeMessage(data.avg_workout_time_min ?? 0)}
          />

          <FitnessCard
            label="Avg Calories / Workout"
            value={`${data.avg_calories_per_workout ?? 0} kcal`}
            note={getAvgCaloriesPerWorkoutMessage(
              data.avg_calories_per_workout ?? 0
            )}
          />
        </div>
      </Slide>

      <Slide>
        <motion.h3
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-4xl font-semibold text-zinc-100"
        >
          Workouts per Month
        </motion.h3>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-lg text-zinc-400 max-w-xl"
        >
          Here’s how often you showed up for each month:
        </motion.p>

        <WorkoutTimelineChart workouts={data.workouts_monthly} />
      </Slide>

      {/* FINAL SUMMARY */}
      <FinalSummarySlide
        movementSteps={data.steps_total}
        sleepHours={Math.round(data.total_net_sleep_hours)}
        fastestPace={data.fastest_pace_min_per_km ?? null}
        totalCaloriesBurned={data.total_workout_calories ?? 0}
      />
    </div>
  );
}

/* ---------------------- */
/* REUSABLE SUBCOMPONENTS */
/* ---------------------- */

function Divider({ label }: { label: string }) {
  return (
    <section className="snap-start py-24 text-center">
      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-5xl font-semibold text-zinc-200 tracking-tight"
      >
        {label}
      </motion.h2>
    </section>
  );
}

function MovementIntro() {
  return (
    <section className="snap-start h-screen flex flex-col items-center justify-center text-center px-8 bg-gradient-to-b from-black via-zinc-950 to-black">
      <motion.span
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-sm uppercase tracking-[0.5em] text-sky-400"
      >
        How you moved this year
      </motion.span>

      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.2 }}
        className="text-7xl md:text-8xl font-black tracking-tight mt-4"
      >
        Movement Summary
      </motion.h2>
    </section>
  );
}

function SleepIntro() {
  return (
    <section className="snap-start h-screen flex flex-col items-center justify-center text-center px-8 bg-gradient-to-t from-black via-zinc-950 to-black">
      <motion.span
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-sm uppercase tracking-[0.5em] text-purple-400"
      >
        How you recharged
      </motion.span>

      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.2 }}
        className="text-7xl md:text-8xl font-black tracking-tight mt-4"
      >
        Sleep Summary
      </motion.h2>
    </section>
  );
}

function RunningIntro() {
  return (
    <section className="snap-start h-screen flex flex-col items-center justify-center text-center px-8 bg-gradient-to-b from-black via-zinc-950 to-black">
      <motion.span
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-sm uppercase tracking-[0.5em] text-emerald-400"
      >
        Big Steppa
      </motion.span>

      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.2 }}
        className="text-7xl md:text-8xl font-black tracking-tight mt-4"
      >
        Running Summary
      </motion.h2>
    </section>
  );
}

function FitnessIntro() {
  return (
    <section className="snap-start h-screen flex flex-col items-center justify-center text-center px-8 bg-gradient-to-b from-black via-slate-950 to-black">
      <motion.span
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-sm uppercase tracking-[0.5em] text-sky-400"
      >
        Sweat, stand, repeat
      </motion.span>

      <motion.h2
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.2 }}
        className="text-7xl md:text-8xl font-black tracking-tight mt-4"
      >
        Fitness Summary
      </motion.h2>
    </section>
  );
}

function Slide({ children }: { children: React.ReactNode }) {
  return (
    <section className="snap-start min-h-screen flex flex-col items-center justify-center px-6 text-center gap-10">
      {children}
    </section>
  );
}

function StatBig({
  value,
  label,
  color,
  size,
}: {
  value: string | number;
  label: string;
  color: string;
  size?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.9 }}
      className={`${size ?? "text-6xl"} font-extrabold bg-gradient-to-br ${color} bg-clip-text text-transparent`}
    >
      {value}
      <p className="mt-4 text-2xl text-zinc-300">{label}</p>
    </motion.div>
  );
}

function StatRow({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="text-2xl text-zinc-300 flex flex-col"
    >
      <span className="font-semibold text-zinc-100">{value}</span>
      <span className="opacity-70 text-lg">{label}</span>
    </motion.div>
  );
}

function SleepCard({
  label,
  value,
  note,
  footer,
}: {
  label: string;
  value: string;
  note?: string;
  footer?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="rounded-3xl border border-purple-400/30 bg-purple-500/5 backdrop-blur px-8 py-10 text-left flex flex-col gap-4 shadow-[0_0_60px_rgba(168,85,247,0.25)]"
    >
      <span className="text-sm uppercase tracking-[0.4em] text-purple-200/80">
        {label}
      </span>

      <span className="text-4xl font-bold text-white">{value}</span>

      {note && <p className="text-sm text-zinc-300">{note}</p>}

      {footer && (
        <span className="text-xs text-purple-200/70">Day: {footer}</span>
      )}
    </motion.div>
  );
}

function RunCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="rounded-3xl border border-emerald-500/20 bg-emerald-500/5 backdrop-blur px-8 py-10 text-left flex flex-col gap-4"
    >
      <span className="text-sm uppercase tracking-[0.4em] text-emerald-300">
        {label}
      </span>

      <span className="text-4xl font-bold text-white">{value}</span>

      {note && <p className="text-sm text-emerald-100/80">{note}</p>}
    </motion.div>
  );
}

function FitnessCard({
  label,
  value,
  note,
  variant = "default",
}: {
  label: string;
  value: string;
  note?: string;
  variant?: "default" | "alert";
}) {
  const isAlert = variant === "alert";
  const border = isAlert ? "border-rose-500/40" : "border-sky-400/30";
  const background = isAlert ? "bg-rose-500/10" : "bg-sky-500/10";
  const text = isAlert ? "text-rose-200" : "text-sky-200";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className={`rounded-3xl border ${border} ${background} backdrop-blur px-8 py-10 text-left flex flex-col gap-4`}
    >
      <span className={`text-sm uppercase tracking-[0.4em] ${text}`}>
        {label}
      </span>

      <span className="text-4xl font-bold text-white">{value}</span>

      {note && <p className="text-sm text-white/70">{note}</p>}
    </motion.div>
  );
}

function FinalSummarySlide({
  movementSteps,
  sleepHours,
  fastestPace,
  totalCaloriesBurned,
}: {
  movementSteps: number;
  sleepHours: number;
  fastestPace: number | null;
  totalCaloriesBurned: number;
}) {
  return (
    <section className="snap-start min-h-screen flex items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        whileInView={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.9 }}
        className="w-full max-w-5xl rounded-[48px] border border-white/10 bg-gradient-to-br from-purple-900/40 via-black to-emerald-900/20 p-10 md:p-14 text-left"
      >
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-10">
          <div>
            <p className="text-sm uppercase tracking-[0.6em] text-zinc-400">
              Wrapped Finale
            </p>
            <h3 className="text-5xl md:text-6xl font-black mt-3">
              Your year at a glance
            </h3>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SummaryTile
            title="Movement"
            stat={`${movementSteps.toLocaleString()} steps`}
            note="Stride after stride, you kept the beat."
            theme="movement"
          />

          <SummaryTile
            title="Sleep"
            stat={`${sleepHours.toLocaleString()} hrs`}
            note="Dream bank fully credited."
            theme="sleep"
          />

          <SummaryTile
            title="Running"
            stat={fastestPace ? `${fastestPace} min/km` : "—"}
            note="Pace so smooth it deserves its own playlist."
            theme="running"
          />

          <SummaryTile
            title="Fitness"
            stat={`${totalCaloriesBurned.toLocaleString()} kcal`}
            note="Calories burned like an endless encore."
            theme="fitness"
          />
        </div>
      </motion.div>
    </section>
  );
}

function SummaryTile({
  title,
  stat,
  note,
  theme,
}: {
  title: string;
  stat: string;
  note: string;
  theme: "movement" | "sleep" | "running" | "fitness";
}) {
  const styles = {
    movement: {
      border: "border-emerald-400/40",
      bg: "bg-emerald-500/10",
      accent: "text-emerald-200",
    },
    sleep: {
      border: "border-purple-400/40",
      bg: "bg-purple-500/10",
      accent: "text-purple-200",
    },
    running: {
      border: "border-sky-400/40",
      bg: "bg-sky-500/10",
      accent: "text-sky-200",
    },
    fitness: {
      border: "border-rose-400/40",
      bg: "bg-rose-500/10",
      accent: "text-rose-200",
    },
  } as const;

  const themeStyles = styles[theme];

  return (
    <div
      className={`rounded-3xl border ${themeStyles.border} ${themeStyles.bg} p-8 flex flex-col gap-3`}
    >
      <span
        className={`text-xs uppercase tracking-[0.5em] ${themeStyles.accent}`}
      >
        {title}
      </span>

      <span className="text-3xl font-bold text-white">{stat}</span>

      <span className="text-sm text-zinc-300">{note}</span>
    </div>
  );
}

/* ---------------------- */
/* MONTHLY STEPS CHART */
/* ---------------------- */

function MonthlyStepsChart({ steps }: { steps?: { [key: number]: number } }) {
  const safeSteps = steps ?? {};

  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  const data = months.map((m, i) => {
    const idx = i + 1;
    const val =
      (safeSteps as any)[idx] ?? (safeSteps as any)[String(idx)] ?? 0;
    return { name: m, steps: val };
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 1 }}
      className="w-full max-w-2xl h-72 mt-8"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.15)" />
          <XAxis dataKey="name" stroke="#aaa" />
          <YAxis stroke="#aaa" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "none",
              borderRadius: 4,
            }}
          />
          <Line
            type="monotone"
            dataKey="steps"
            stroke="#a855f7"
            strokeWidth={3}
            dot={{ fill: "#a855f7", r: 4 }}
            activeDot={{ r: 8 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

/* ---------------------- */
/* MONTHLY WORKOUTS CHART */
/* ---------------------- */

function WorkoutTimelineChart({
  workouts,
}: {
  workouts?: { [key: number]: number };
}) {
  const safeWorkouts = workouts ?? {};

  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  const data = months.map((m, i) => {
    const idx = i + 1;
    const val =
      (safeWorkouts as any)[idx] ?? (safeWorkouts as any)[String(idx)] ?? 0;
    return { name: m, workouts: val };
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 1 }}
      className="w-full max-w-2xl h-72 mt-8"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.15)" />
          <XAxis
            dataKey="name"
            stroke="#aaa"
            label={{
              value: "Months",
              position: "insideBottom",
              offset: -5,
              fill: "#aaa",
            }}
          />
          <YAxis
            stroke="transparent"
            tick={false}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "none",
              borderRadius: 4,
            }}
          />
          <Bar dataKey="workouts" fill="#10b981" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

/* ---------------------- */
/* MESSAGE HELPERS */
/* ---------------------- */

function getStepsMessage(steps: number): string {
  if (steps < 50000)
    return "Whoa... did your sneakers go on vacation? Your couch definitely won this year.";
  if (steps < 200000)
    return "You kept things casual—enough movement to keep the playlists going, but room to roam.";
  if (steps < 500000)
    return "You were active! That many steps is basically a never-ending city stroll.";
  return "Holy moly cuz... that's alot of steps!";
}

function getDistanceMessage(km: number): string {
  if (km >= 1500) return "That's like walking from Toronto to Minnesota!";
  if (km >= 800)
    return "You covered enough ground to stretch across a couple of countries.";
  if (km >= 200)
    return "Solid grind: that’s a full-on road trip completed one stride at a time.";
  return "Every kilometer counts—keep stacking them and the map won’t keep up.";
}

function getFlightsMessage(flights: number): string {
  if (flights === 0)
    return "Elevators only? No judgement, but even your smartwatch is side-eyeing you.";
  if (flights < 200)
    return "Steady climbs! You treated stairs like background dancers.";
  if (flights < 500)
    return "You and staircases? Basically on a first-name basis.";
  return "All this cardio warrants skipping every single leg day";
}

function getSleepHoursMessage(hours: number): string {
  if (hours > 3000)
    return "This year was part bedtime story, part hibernation docuseries.";
  if (hours > 2000)
    return "Consider yourself well-rested royalty—crowns made of pillows.";
  return "Sleep was a bit of a speedrun :(";
}

function getBedtimeMessage(bedtime?: string): string {
  if (!bedtime) return "Bedtime mystery unlocked soon.";
  return bedtime > "23:00"
    ? "Night owl confirmed—you love the late-night vibes."
    : "Pretty tidy bedtime. Your circadian rhythm approves.";
}

function getWakeMessage(waketime?: string): string {
  if (!waketime) return "Wake time? Still buffering.";
  return waketime < "07:00"
    ? "Early bird energy—you probably saw a few sunrises."
    : "You vibe with the snooze button and we're here for it.";
}

function getRestlessNightMessage(awakeningCount?: number): string {
  if (!awakeningCount) return "Quite the restless night!";
  if (awakeningCount > 10) return "Quite the restless night!";
  return "A few tosses and turns, but you made it through.";
}

function getLongestSleepMessage(hours?: number): string {
  if (!hours) return "Quite the slumber.";
  if (hours >= 12)
    return "Quite the slumber—did you awaken in another era?";
  return "Big slumber time";
}

function getShortestSleepMessage(hours?: number): string {
  if (!hours) return "Power nap vibes.";
  if (hours <= 3) return "Basically a blink LOL";
  return "Blink and you missed that night.";
}

function getRunCountMessage(runs: number): string {
  if (runs === 0)
    return "Your running shoes are in mint condition. Maybe too mint.";
  if (runs < 20) return "Quality over quantity I suppose.";
  if (runs < 60)
    return "Steady rhythm. Those playlists got some mileage.";
  return "You basically lived on the leaderboard.";
}

function getLongestRunMessage(km: number): string {
  if (km >= 30) return "Marathon-core unlocked. That’s an epic long run.";
  if (km >= 15)
    return "Long enough to cross a couple neighborhoods with bragging rights.";
  return "Bent the corner.";
}

function getFastestPaceMessage(pace: number | null): string {
  if (!pace) return "Pace radar couldn’t lock on—mysterious speed!";
  if (pace < 4) return "Blazing. You left even the data catching its breath.";
  if (pace < 5.5) return "Swift and smooth—you floated through those runs.";
  return "Vibez and cardio.";
}

function getRunDistanceMessage(km: number): string {
  if (km >= 500) return "That's a legit tour of the map. Passport stamps pending.";
  if (km >= 200)
    return "Hundreds of kilometers, countless playlists finished.";
  return "Every kilometer counts.";
}

function getExerciseMinutesMessage(minutes: number): string {
  if (minutes >= 2000)
    return "Time is muscle—you basically lived in workout mode.";
  if (minutes >= 1000) return "Hours kept stackin.";
  return "Every minute mattered. Warm-up phase complete.";
}

function getCaloriesBurnedMessage(calories: number): string {
  if (calories >= 100000)
    return "That’s enough energy to light up the block.";
  if (calories >= 50000)
    return "Plenty of sweat equity invested this year.";
  return "A solid burn to get started.";
}

function getStandHoursMessage(hours: number): string {
  if (hours >= 500) return "CHAIRS EXIST BRO";
  if (hours >= 300)
    return "You logged serious stand hours; the chair missed you.";
  return "Baby steps toward less sitting. Keep it up.";
}

function getWorkoutBPMMessage(value: number, type: "high" | "avg"): string {
  if (type === "high") {
    if (value >= 190) return "We hittin heart till failure or what";
    if (value >= 160) return "You pushed into the spicy zone whenever it mattered.";
    return "A composed high—power with control.";
  }

  if (value >= 150) return "Your baseline intensity is pretty fiery.";
  if (value >= 120) return "Smooth operator";
  return "Chill sessions. Maybe next season gets a remix?";
}

function getAvgWorkoutTimeMessage(minutes: number): string {
  if (minutes >= 60) return "Sessions long enough to count as mini-epics.";
  if (minutes >= 30) return "Perfectly portioned workouts.";
  return "Quick hits, maximum efficiency. HIIT energy.";
}

function getAvgCaloriesPerWorkoutMessage(calories: number): string {
  if (calories >= 600) return "Every workout was a blockbuster burn.";
  if (calories >= 350)
    return "A consistent burn that kept stacking up.";
  return "Light and breezy.";
}
