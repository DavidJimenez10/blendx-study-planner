import {
  Badge,
  Button,
  Group,
  Loader,
  Menu,
  Progress,
  Text,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconArrowLeft,
  IconCalendar,
  IconCircleCheck,
  IconClock,
  IconPlus,
  IconSparkles,
  IconTarget,
} from "@tabler/icons-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, type StudyTask } from "../../api/client";
import AddTaskModal from "../../components/task/AddTaskModal";
import TaskItem from "../../components/task/TaskItem";
import styles from "./PlanDetail.module.css";

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export default function PlanDetail() {
  const { planId } = useParams<{ planId: string }>();
  const id = Number(planId);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [addTaskOpened, { open: openAddTask, close: closeAddTask }] =
    useDisclosure(false);

  const [genWarning, setGenWarning] = useState<string | null>(null);

  const { data: plan, isLoading: planLoading } = useQuery({
    queryKey: ["plan", id],
    queryFn: () => api.getPlan(id),
    enabled: !!id,
  });

  const { data: tasks = [], isLoading: tasksLoading } = useQuery<StudyTask[]>({
    queryKey: ["tasks", id],
    queryFn: () => api.getTasks(id),
    enabled: !!id,
  });

  const toggleTask = useMutation({
    mutationFn: ({
      taskId,
      completed,
    }: {
      taskId: number;
      completed: boolean;
    }) => api.toggleTask(id, taskId, completed),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", id] });
      qc.invalidateQueries({ queryKey: ["taskStats"] });
    },
  });

  const generateTasks = useMutation({
    mutationFn: () => api.generateTasks(id),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["tasks", id] });
      setGenWarning(null);
      if (data.warning) {
        setGenWarning(data.warning);
      } else if (data.failed_generations.length > 0) {
        setGenWarning(
          `${data.tasks.length} task(s) created, ${data.failed_generations.length} failed validation.`,
        );
      }
    },
    onError: (error: Error) => {
      setGenWarning(error.message || "Generation failed");
    },
  });

  const completedCount = tasks.filter((t) => t.completed).length;
  const totalCount = tasks.length;
  const isComplete = totalCount > 0 && completedCount === totalCount;
  const progressPct =
    totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
  const totalHours = tasks.reduce((s, t) => s + t.estimated_hours, 0);

  if (planLoading) {
    return (
      <div className={styles.loadingPage}>
        <Loader color="cyan" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className={styles.loadingPage}>
        <Text c="dimmed">Plan not found.</Text>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Group gap="sm">
          <button className={styles.backBtn} onClick={() => navigate("/")}>
            <IconArrowLeft size={16} />
          </button>
          <Text className={styles.breadcrumb} onClick={() => navigate("/")}>
            Plans
          </Text>
          <Text className={styles.breadcrumbSep}>/</Text>
          <Text className={styles.breadcrumbCurrent}>{plan.goal}</Text>
        </Group>
      </header>

      <main className={styles.main}>
        <div
          className={`${styles.planCard} ${isComplete ? styles.planCardComplete : ""}`}
        >
          <div className={styles.planCardInner}>
            <div>
              <Text className={styles.planLabel}>Goal</Text>
              <Title order={2} className={styles.planGoal}>
                {plan.goal}
              </Title>
              {plan.description && (
                <Text className={styles.planDescription}>
                  {plan.description}
                </Text>
              )}
            </div>
            <div className={styles.planMeta}>
              <Group gap="lg" wrap="wrap">
                <Group gap={6}>
                  <IconClock size={14} color="var(--c-turquoise)" />
                  <Text className={styles.metaText}>
                    {plan.hours_per_week}h / week
                  </Text>
                </Group>
                {plan.target_date && (
                  <Group gap={6}>
                    <IconCalendar size={14} color="var(--c-turquoise)" />
                    <Text className={styles.metaText}>
                      {formatDate(plan.target_date)}
                    </Text>
                  </Group>
                )}
                <Group gap={6}>
                  <IconTarget size={14} color="var(--c-turquoise)" />
                  <Text className={styles.metaText}>
                    {completedCount}/{totalCount} tasks
                  </Text>
                </Group>
              </Group>
              {totalCount > 0 && (
                <Progress
                  value={progressPct}
                  color={isComplete ? "teal" : "cyan"}
                  size="sm"
                  className={styles.planProgress}
                />
              )}
            </div>
          </div>
        </div>

        <div className={styles.tasksSection}>
          <Group justify="space-between" mb="lg">
            <Title order={4} className={styles.tasksTitle}>
              Tasks
            </Title>
            <Group gap="sm">
              {tasks.length > 0 && (
                <Badge color="cyan" variant="light" size="sm">
                  {totalHours}h total
                </Badge>
              )}
              <Menu position="bottom-end" shadow="md" width={180}>
                <Menu.Target>
                  <Button
                    leftSection={<IconPlus size={13} />}
                    color="cyan"
                    size="xs"
                    variant="light"
                  >
                    Add task
                  </Button>
                </Menu.Target>
                <Menu.Dropdown>
                  <Menu.Item
                    leftSection={<IconPlus size={14} />}
                    onClick={openAddTask}
                  >
                    Add manually
                  </Menu.Item>
                  <Menu.Item
                    leftSection={<IconSparkles size={14} />}
                    onClick={() => generateTasks.mutate()}
                    disabled={!plan?.target_date || generateTasks.isPending}
                  >
                    {generateTasks.isPending
                      ? "Generating\u2026"
                      : "Generate with AI"}
                  </Menu.Item>
                </Menu.Dropdown>
              </Menu>
            </Group>
          </Group>

          {genWarning && (
            <Text
              size="sm"
              mb="md"
              style={{
                fontFamily: "var(--font)",
                padding: "0.5rem 0.75rem",
                borderRadius: "6px",
                background: genWarning.includes("failed")
                  ? "rgba(255, 184, 0, 0.08)"
                  : "rgba(255, 184, 0, 0.08)",
                color: genWarning.includes("Generation failed")
                  ? "var(--c-danger, #ff6b6b)"
                  : "var(--c-warning, #ffb800)",
              }}
            >
              {genWarning}
            </Text>
          )}

          {generateTasks.isPending ? (
            <div className={styles.loader}>
              <Loader color="cyan" size="sm" />
              <Text
                size="sm"
                c="dimmed"
                ml="sm"
                style={{ fontFamily: "var(--font)" }}
              >
                Generating tasks...
              </Text>
            </div>
          ) : (
            <>
              {isComplete && (
                <div className={styles.completionBanner}>
                  <IconCircleCheck size={20} color="var(--c-turquoise)" />
                  <div>
                    <Text className={styles.completionTitle}>
                      All tasks complete
                    </Text>
                    <Text className={styles.completionSub}>
                      Great work — you've finished every task in this plan.
                    </Text>
                  </div>
                </div>
              )}

              {tasksLoading ? (
                <div className={styles.loader}>
                  <Loader color="cyan" size="sm" />
                </div>
              ) : tasks.length === 0 ? (
                <div className={styles.emptyTasks}>
                  <IconTarget size={32} stroke={1.2} color="var(--c-cool-gray)" />
                  <Text className={styles.emptyText}>
                    No tasks yet. Break your goal into actionable steps.
                  </Text>
                </div>
              ) : (
                <div className={styles.taskList}>
                  {tasks.map((task) => (
                    <TaskItem
                      key={task.id}
                      task={task}
                      onToggle={(taskId, completed) =>
                        toggleTask.mutate({ taskId, completed })
                      }
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </main>

      <AddTaskModal opened={addTaskOpened} onClose={closeAddTask} planId={id} />
    </div>
  );
}
