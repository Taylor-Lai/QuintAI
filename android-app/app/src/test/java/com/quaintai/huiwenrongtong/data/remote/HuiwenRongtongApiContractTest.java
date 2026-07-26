package com.quaintai.huiwenrongtong.data.remote;

import static org.junit.Assert.assertEquals;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.junit.Test;
import retrofit2.http.DELETE;
import retrofit2.http.GET;
import retrofit2.http.PATCH;
import retrofit2.http.POST;
import retrofit2.http.PUT;

public class HuiwenRongtongApiContractTest {
    @Test
    public void androidClientExposesEveryWebApiRoute() {
        Set<String> actual = new HashSet<>();
        for (Method method : HuiwenRongtongApi.class.getMethods()) {
            if (method.isAnnotationPresent(GET.class)) actual.add("GET " + method.getAnnotation(GET.class).value());
            if (method.isAnnotationPresent(POST.class)) actual.add("POST " + method.getAnnotation(POST.class).value());
            if (method.isAnnotationPresent(PUT.class)) actual.add("PUT " + method.getAnnotation(PUT.class).value());
            if (method.isAnnotationPresent(PATCH.class)) actual.add("PATCH " + method.getAnnotation(PATCH.class).value());
            if (method.isAnnotationPresent(DELETE.class)) actual.add("DELETE " + method.getAnnotation(DELETE.class).value());
        }

        Set<String> expected = new HashSet<>(Arrays.asList(
            "POST auth/login", "POST auth/register", "POST auth/logout", "POST auth/heartbeat",
            "GET user/profile", "PUT user/profile", "GET tasks", "GET tasks/{id}",
            "GET tasks/{id}/report", "GET tasks/{id}/download", "POST tasks/{id}/retry", "POST tasks/{id}/cancel",
            "GET workspace/overview", "POST workspace/demo", "GET workspace/documents", "POST workspace/documents",
            "PATCH workspace/documents/{id}", "DELETE workspace/documents/{id}", "GET workspace/documents/{id}/download",
            "GET workspace/reviews", "GET workspace/reviews/{id}", "PUT workspace/reviews/{id}",
            "POST workspace/reviews/{id}/auto-fix", "GET workspace/workflows", "POST workspace/workflows",
            "PUT workspace/workflows/{id}", "DELETE workspace/workflows/{id}", "POST workspace/workflows/{id}/runs",
            "GET workspace/workflow-runs", "GET enterprise/dashboard", "GET enterprise/organization",
            "GET enterprise/organizations", "POST enterprise/organizations/{id}/activate", "PUT enterprise/organization",
            "POST enterprise/members", "PUT enterprise/members/{id}", "DELETE enterprise/members/{id}",
            "GET enterprise/audit-logs", "GET enterprise/api-keys", "POST enterprise/api-keys",
            "DELETE enterprise/api-keys/{id}", "GET enterprise/webhooks", "POST enterprise/webhooks",
            "DELETE enterprise/webhooks/{id}", "POST enterprise/webhooks/{id}/test", "GET enterprise/webhook-deliveries",
            "GET enterprise/knowledge", "POST enterprise/knowledge", "POST enterprise/knowledge/{id}/documents",
            "GET enterprise/knowledge/{id}/documents", "GET enterprise/knowledge/{id}/search",
            "GET enterprise/knowledge/{id}/graph", "GET enterprise/schedules", "POST enterprise/schedules",
            "DELETE enterprise/schedules/{id}", "PUT enterprise/subscription", "GET enterprise/operations",
            "GET enterprise/backups", "POST enterprise/backups", "GET enterprise/comments", "POST enterprise/comments",
            "PATCH enterprise/comments/{id}/resolve", "GET enterprise/documents/{id}/versions",
            "POST enterprise/documents/{id}/versions", "GET admin/statistics", "GET admin/users",
            "GET admin/users/{id}", "DELETE admin/users/{id}", "PUT admin/users/{id}/role",
            "PUT admin/users/{id}/status", "POST doc-chat/upload", "POST doc-extract/upload", "POST table-fill/upload"
        ));

        assertEquals("Web and Android API contracts differ", expected, actual);
    }
}
