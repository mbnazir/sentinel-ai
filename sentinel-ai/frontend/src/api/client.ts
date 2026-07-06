import axios from "axios";
import type { ApiResponse, InvestigationCase, InvestigationNarrative } from "../types";
import type { TimelineVisualizationData } from "../timelineTypes";

const client = axios.create({
  baseURL: "/api/v1/workflow",
  timeout: 30000
});

export async function fetchInvestigationCases(): Promise<InvestigationCase[]> {
  const response = await client.get<ApiResponse<InvestigationCase[]>>("/investigations");
  return response.data.data;
}

export async function assignInvestigation(caseId: string, assigneeId: string): Promise<InvestigationCase> {
  const response = await client.post<ApiResponse<InvestigationCase>>(`/investigations/${caseId}/assign`, {
    assignee_id: assigneeId
  });
  return response.data.data;
}

export async function transitionInvestigation(caseId: string, targetStatus: string): Promise<InvestigationCase> {
  const response = await client.post<ApiResponse<InvestigationCase>>(`/investigations/${caseId}/transition`, {
    target_status: targetStatus
  });
  return response.data.data;
}

export async function addInvestigationComment(
  caseId: string,
  authorId: string,
  body: string
): Promise<InvestigationCase> {
  const response = await client.post<ApiResponse<InvestigationCase>>(`/investigations/${caseId}/comments`, {
    author_id: authorId,
    body
  });
  return response.data.data;
}

export async function generateNarrative(caseId: string): Promise<InvestigationNarrative> {
  const response = await client.post<ApiResponse<InvestigationNarrative>>(`/investigations/${caseId}/narrative`);
  return response.data.data;
}


const timelineClient = axios.create({
  baseURL: "/api/v1/timelines",
  timeout: 30000
});

export async function fetchTimelineVisualization(loginSessionExternalId: string): Promise<TimelineVisualizationData> {
  const response = await timelineClient.get<ApiResponse<TimelineVisualizationData>>(`/${loginSessionExternalId}`);
  return response.data.data;
}
