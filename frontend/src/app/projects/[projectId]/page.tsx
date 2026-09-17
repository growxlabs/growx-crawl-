import { redirect } from "next/navigation";

export default function ProjectRootRedirect({
  params,
}: {
  params: { projectId: string };
}) {
  redirect(`/projects/${params.projectId}/overview`);
}
