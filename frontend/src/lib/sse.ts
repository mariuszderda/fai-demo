import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { API_BASE } from "./api";

type StreamEventPayload = Record<string, unknown>;
type StreamSnapshot = Record<string, StreamEventPayload>;

type Subscriber = () => void;

const connectedIncidentIds = new Set<string>();
const subscribers = new Set<Subscriber>();

function emitConnectionUpdate(): void {
  for (const subscriber of subscribers) {
    subscriber();
  }
}

function setIncidentConnected(incidentId: string, connected: boolean): void {
  const before = connectedIncidentIds.has(incidentId);
  if (connected) {
    connectedIncidentIds.add(incidentId);
  } else {
    connectedIncidentIds.delete(incidentId);
  }
  if (before !== connected) {
    emitConnectionUpdate();
  }
}

function subscribeToConnections(subscriber: Subscriber): () => void {
  subscribers.add(subscriber);
  return () => {
    subscribers.delete(subscriber);
  };
}

function getConnectionSnapshot(): boolean {
  return connectedIncidentIds.size > 0;
}

function buildPayload(eventType: string, data: unknown): StreamEventPayload {
  return {
    eventType,
    payload: data,
    receivedAt: new Date().toISOString(),
  };
}

function invalidationKeys(incidentId: string, eventType: string): Array<Array<string>> {
  switch (eventType) {
    case "pipeline_step":
      return [["incident", incidentId]];
    case "ioc_extracted":
    case "ioc_review_requested":
    case "ioc_review_finalized":
      return [["incident", incidentId], ["ioc", incidentId]];
    case "approval_pending":
    case "approval_decided":
      return [["incident", incidentId], ["approvals"]];
    case "report_ready":
      return [["incident", incidentId]];
    default:
      return [["incident", incidentId]];
  }
}

export function useAnyIncidentStreamConnected(): boolean {
  return useSyncExternalStore(subscribeToConnections, getConnectionSnapshot, getConnectionSnapshot);
}

export function useIncidentStream(incidentId: string | null): {
  connected: boolean;
  lastEvent: StreamSnapshot;
} {
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<StreamSnapshot>({});

  const endpoint = useMemo(() => {
    if (!incidentId) {
      return null;
    }
    return `${API_BASE}/api/v1/incidents/${incidentId}/stream`;
  }, [incidentId]);

  useEffect(() => {
    if (!endpoint || !incidentId) {
      setConnected(false);
      return;
    }

    const source = new EventSource(endpoint);
    const eventTypes = [
      "pipeline_step",
      "ioc_extracted",
      "ioc_review_requested",
      "ioc_review_finalized",
      "approval_pending",
      "approval_decided",
      "report_ready",
      "heartbeat",
      "message",
    ];

    const handleOpen = (): void => {
      setConnected(true);
      setIncidentConnected(incidentId, true);
    };

    const handleError = (): void => {
      setConnected(false);
      setIncidentConnected(incidentId, false);
    };

    const handleEvent = (event: Event): void => {
      const message = event as MessageEvent<string>;
      let data: unknown = {};
      try {
        data = message.data ? JSON.parse(message.data) : {};
      } catch {
        data = { raw: message.data };
      }
      const eventType = event.type || "message";
      setLastEvent((current) => ({
        ...current,
        [eventType]: buildPayload(eventType, data),
      }));
      for (const key of invalidationKeys(incidentId, eventType)) {
        void queryClient.invalidateQueries({ queryKey: key });
      }
    };

    source.addEventListener("open", handleOpen);
    source.addEventListener("error", handleError);
    for (const eventType of eventTypes) {
      source.addEventListener(eventType, handleEvent);
    }

    return () => {
      source.removeEventListener("open", handleOpen);
      source.removeEventListener("error", handleError);
      for (const eventType of eventTypes) {
        source.removeEventListener(eventType, handleEvent);
      }
      source.close();
      setConnected(false);
      setIncidentConnected(incidentId, false);
    };
  }, [endpoint, incidentId, queryClient]);

  return { connected, lastEvent };
}

