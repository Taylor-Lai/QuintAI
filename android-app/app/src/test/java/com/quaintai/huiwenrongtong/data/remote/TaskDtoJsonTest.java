package com.quaintai.huiwenrongtong.data.remote;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import com.google.gson.Gson;
import org.junit.Test;

public class TaskDtoJsonTest {
    @Test
    public void acceptsNullJsonPayloadsWhileTaskIsQueued() {
        TaskDto task = new Gson().fromJson(
            "{\"id\":\"task-1\",\"kind\":\"document_extract\",\"status\":\"queued\","
                + "\"result\":null,\"quality_report\":null,\"evidence_summary\":null}",
            TaskDto.class
        );

        assertNotNull(task.getResult());
        assertTrue(task.getResult().isJsonNull());
        assertTrue(task.getQualityReport().isJsonNull());
        assertTrue(task.getEvidenceSummary().isJsonNull());
    }
}
