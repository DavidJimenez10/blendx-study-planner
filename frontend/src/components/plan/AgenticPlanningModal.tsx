import {
  ActionIcon,
  Alert,
  Button,
  Group,
  Modal,
  NumberInput,
  Progress,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { IconAlertCircle, IconTrash, IconRobot } from "@tabler/icons-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useCallback } from "react";
import {
  api,
  type Subtopic,
  type TaskDraft,
} from "../../api/client";
import styles from "./AgenticPlanningModal.module.css";

interface Props {
  opened: boolean;
  onClose: () => void;
  planId: number;
}

type Step = "breakdown" | "review" | "generating";

interface StreamState {
  currentSubtopic: string;
  eventIndex: number;
  generatedTasks: TaskDraft[];
  warnings: string[];
  completed: number;
  total: number;
  eventLog: string[];
}

export default function AgenticPlanningModal({
  opened,
  onClose,
  planId,
}: Props) {
  const qc = useQueryClient();
  const [step, setStep] = useState<Step>("breakdown");
  const [subtopics, setSubtopics] = useState<Subtopic[]>([]);
  const [stream, setStream] = useState<StreamState>({
    currentSubtopic: "",
    eventIndex: 0,
    generatedTasks: [],
    warnings: [],
    completed: 0,
    total: 0,
    eventLog: [],
  });
  const [streamError, setStreamError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [planningFinished, setPlanningFinished] = useState(false);

  const indexForm = useForm({
    initialValues: {
      editIndex: -1,
      editName: "",
      editDescription: "",
      editHours: 0,
    },
  });

  const breakdown = useMutation({
    mutationFn: () => api.agentBreakdown(planId),
    onSuccess: (data) => {
      setSubtopics(data.subtopics);
      setStep("review");
    },
  });

  const handleGenerate = useCallback(async () => {
    if (subtopics.length === 0) return;
    setStep("generating");
    setIsGenerating(true);
    setStreamError(null);
    setPlanningFinished(false);
    setStream({
      currentSubtopic: "",
      eventIndex: 0,
      generatedTasks: [],
      warnings: [],
      completed: 0,
      total: 0,
      eventLog: [],
    });

    try {
      const gen = api.agentGenerate(planId, subtopics);
      for await (const sseEvent of gen) {
        console.log("[SSE]", sseEvent.event, sseEvent.data);
        setStream((prev) => {
          switch (sseEvent.event) {
            case "planning_started":
              return {
                ...prev,
                total: sseEvent.data.subtopic_count,
                eventLog: [...prev.eventLog, `Planning ${sseEvent.data.subtopic_count} subtopics...`],
                eventIndex: prev.eventIndex + 1,
              };
            case "subtopic_started":
              return {
                ...prev,
                currentSubtopic: sseEvent.data.subtopic,
                completed: prev.completed + 1,
                generatedTasks: [],
                warnings: [],
                eventLog: [...prev.eventLog, `${sseEvent.data.index}/${sseEvent.data.total} ${sseEvent.data.subtopic}`],
                eventIndex: prev.eventIndex + 1,
              };
            case "tasks_generated":
              return {
                ...prev,
                generatedTasks: sseEvent.data.tasks,
                warnings: [],
                eventLog: [...prev.eventLog, `  ${sseEvent.data.task_count} tasks generated`],
                eventIndex: prev.eventIndex + 1,
              };
            case "validation_retry":
              return {
                ...prev,
                warnings: [
                  `Retrying: ${sseEvent.data.feedback}`,
                ],
                eventLog: [...prev.eventLog, `  Retrying: ${sseEvent.data.feedback}`],
                eventIndex: prev.eventIndex + 1,
              };
            case "warning":
              return {
                ...prev,
                warnings: [...prev.warnings, sseEvent.data.message],
                eventLog: [...prev.eventLog, `  ⚠ ${sseEvent.data.message}`],
                eventIndex: prev.eventIndex + 1,
              };
            case "tasks_saved":
              return {
                ...prev,
                eventLog: [...prev.eventLog, `  Saved to database`],
                eventIndex: prev.eventIndex + 1,
              };
            case "planning_complete":
              setPlanningFinished(true);
              return {
                ...prev,
                eventLog: [...prev.eventLog, "All subtopics complete!"],
              };
            case "error":
              setStreamError(sseEvent.data.message);
              return {
                ...prev,
                eventLog: [...prev.eventLog, `ERROR: ${sseEvent.data.message}`],
              };
            default:
              return prev;
          }
        });
      }
      qc.invalidateQueries({ queryKey: ["tasks", planId] });
      qc.invalidateQueries({ queryKey: ["taskStats"] });
    } catch (e) {
      setStreamError(
        e instanceof Error ? e.message : "Stream connection failed",
      );
    } finally {
      setIsGenerating(false);
    }
  }, [planId, subtopics, qc]);

  function handleRemove(index: number) {
    setSubtopics((prev) => prev.filter((_, i) => i !== index));
  }

  function startEdit(index: number) {
    const s = subtopics[index];
    indexForm.setValues({
      editIndex: index,
      editName: s.name,
      editDescription: s.description,
      editHours: s.suggested_hours,
    });
  }

  function saveEdit() {
    const idx = indexForm.values.editIndex;
    if (idx < 0) return;
    setSubtopics((prev) =>
      prev.map((s, i) =>
        i === idx
          ? {
              name: indexForm.values.editName.trim() || s.name,
              description:
                indexForm.values.editDescription.trim() || s.description,
              suggested_hours: indexForm.values.editHours || s.suggested_hours,
            }
          : s,
      ),
    );
    indexForm.setValues({ editIndex: -1, editName: "", editDescription: "", editHours: 0 });
  }

  function handleClose() {
    setStep("breakdown");
    setSubtopics([]);
    setStream({
      currentSubtopic: "",
      eventIndex: 0,
      generatedTasks: [],
      warnings: [],
      completed: 0,
      total: 0,
      eventLog: [],
    });
    setStreamError(null);
    setIsGenerating(false);
    setPlanningFinished(false);
    breakdown.reset();
    indexForm.reset();
    onClose();
  }

  const overallProgress =
    stream.total > 0 ? Math.round((stream.completed / stream.total) * 100) : 0;

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title="Agentic Planning"
      centered
      size="lg"
      classNames={{ title: styles.modalTitle }}
    >
      {/* Step 1: Breakdown */}
      {step === "breakdown" && (
        <Stack gap="md" align="center" py="md">
          <IconRobot size={40} stroke={1.2} color="var(--c-turquoise)" />
          <Text size="sm" c="dimmed">
            The AI will analyze your study plan and break it down into
            subtopics. You can review and edit them before generating tasks.
          </Text>
          {breakdown.isError && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="red"
              variant="light"
              p="sm"
              w="100%"
            >
              {breakdown.error instanceof Error
                ? breakdown.error.message
                : "Breakdown failed"}
            </Alert>
          )}
          <Button
            color="cyan"
            onClick={() => breakdown.mutate()}
            loading={breakdown.isPending}
            leftSection={<IconRobot size={18} />}
          >
            Analyze Plan
          </Button>
        </Stack>
      )}

      {/* Step 2: Review */}
      {step === "review" && (
        <Stack gap="md">
          <Title order={4} className={styles.sectionTitle}>
            Review Subtopics ({subtopics.length})
          </Title>
          <Text size="sm" c="dimmed">
            Edit, remove, or confirm the subtopics below. The AI will generate
            tasks tailored to each one.
          </Text>

          <div className={styles.subtopicList}>
            {subtopics.map((s, i) =>
              indexForm.values.editIndex === i ? (
                <div key={i} className={styles.editRow}>
                  <TextInput
                    label="Name"
                    value={indexForm.values.editName}
                    onChange={(e) =>
                      indexForm.setFieldValue("editName", e.currentTarget.value)
                    }
                  />
                  <TextInput
                    label="Description"
                    value={indexForm.values.editDescription}
                    onChange={(e) =>
                      indexForm.setFieldValue(
                        "editDescription",
                        e.currentTarget.value,
                      )
                    }
                  />
                  <NumberInput
                    label="Hours"
                    min={0.5}
                    step={0.5}
                    max={200}
                    value={indexForm.values.editHours}
                    onChange={(v) =>
                      indexForm.setFieldValue("editHours", Number(v) || 0)
                    }
                  />
                  <Group justify="flex-end">
                    <Button
                      variant="subtle"
                      size="xs"
                      color="gray"
                      onClick={() =>
                        indexForm.setValues({
                          editIndex: -1,
                          editName: "",
                          editDescription: "",
                          editHours: 0,
                        })
                      }
                    >
                      Cancel
                    </Button>
                    <Button size="xs" color="cyan" onClick={saveEdit}>
                      Save
                    </Button>
                  </Group>
                </div>
              ) : (
                <Group key={i} className={styles.subtopicRow} wrap="nowrap" gap="sm">
                  <div className={styles.subtopicInfo}>
                    <Text className={styles.subtopicName}>{s.name}</Text>
                    <Text className={styles.subtopicMeta}>
                      {s.description} &middot; {s.suggested_hours}h
                    </Text>
                  </div>
                  <Group gap={4} wrap="nowrap">
                    <Button
                      variant="subtle"
                      size="xs"
                      color="gray"
                      onClick={() => startEdit(i)}
                    >
                      Edit
                    </Button>
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      size="sm"
                      onClick={() => handleRemove(i)}
                    >
                      <IconTrash size={14} />
                    </ActionIcon>
                  </Group>
                </Group>
              ),
            )}
            {subtopics.length === 0 && (
              <Text size="sm" c="dimmed" ta="center" py="md">
                No subtopics. Close and try again.
              </Text>
            )}
          </div>

          <Group justify="flex-end" mt="xs">
            <Button
              variant="subtle"
              color="gray"
              onClick={() => setStep("breakdown")}
            >
              Back
            </Button>
            <Button
              color="cyan"
              onClick={handleGenerate}
              disabled={subtopics.length === 0 || isGenerating}
              loading={isGenerating}
              leftSection={<IconRobot size={18} />}
            >
              Generate Tasks
            </Button>
          </Group>
        </Stack>
      )}

      {/* Step 3: Generating */}
      {step === "generating" && (
        <Stack gap="md" py="md">
          <Title order={4} className={styles.sectionTitle}>
            Generating Tasks
          </Title>

          <Progress
            value={overallProgress}
            color="cyan"
            size="sm"
            animated={isGenerating}
          />

          {stream.total > 0 && (
            <Text size="xs" c="dimmed" ta="center">
              {stream.completed} of {stream.total} subtopics complete
            </Text>
          )}

          {stream.currentSubtopic && (
            <div className={styles.streamBlock}>
              <Text className={styles.streamLabel}>
                {stream.currentSubtopic}
              </Text>
              <div className={styles.streamEvents}>
                {stream.eventLog.map((line, i) => (
                  <Text key={i} className={styles.streamEvent}>
                    {line}
                  </Text>
                ))}
              </div>
            </div>
          )}

          {!stream.currentSubtopic && stream.eventLog.length > 0 && (
            <div className={styles.streamBlock}>
              <div className={styles.streamEvents}>
                {stream.eventLog.map((line, i) => (
                  <Text key={i} className={styles.streamEvent}>
                    {line}
                  </Text>
                ))}
              </div>
            </div>
          )}

          {!isGenerating && !streamError && planningFinished && (
            <Alert color="green" variant="light" p="sm" ta="center">
              All tasks generated successfully!
            </Alert>
          )}

          {!isGenerating && !planningFinished && streamError && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="red"
              variant="light"
              p="sm"
            >
              {streamError}
            </Alert>
          )}

          {!isGenerating && !planningFinished && !streamError && stream.total > 0 && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="yellow"
              variant="light"
              p="sm"
              ta="center"
            >
              Generation stopped before completion. The remaining subtopics may
              not have been processed.
            </Alert>
          )}

          <Group justify="center">
            <Button
              color="cyan"
              onClick={handleClose}
              disabled={isGenerating}
            >
              Done
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}
