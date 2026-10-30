import io.javalin.Javalin;
import io.javalin.http.staticfiles.Location;
import io.javalin.websocket.WsContext;
import org.eclipse.paho.client.mqttv3.*;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class Main {
    private static final Set<WsContext> clients = ConcurrentHashMap.newKeySet();

    public static void main(String[] args) {
        Javalin app = Javalin.create(config -> {
            config.staticFiles.add(staticFileConfig -> {
                staticFileConfig.directory = "/app/public";
                staticFileConfig.location = Location.EXTERNAL;
            });
        }).start(8000);

        app.ws("/api/ws", ws -> {
            ws.onConnect(ctx -> clients.add(ctx));
            ws.onClose(ctx -> clients.remove(ctx));
        });

        setupMqtt();

        app.get("/", ctx -> {
            try {
                String html = Files.readString(Paths.get("/app/public/index.html"));
                ctx.html(html);
            } catch (Exception e) {
                ctx.status(404).result("Σφάλμα: Το index.html δεν βρέθηκε!");
            }
        });

        app.get("/api/telemetry", ctx -> {
            String timeRange = ctx.queryParamAsClass("range", String.class).getOrDefault("1h");
            String bucket = "1 minute";
            String interval = "1 hour";
            
            if ("1d".equals(timeRange)) { bucket = "30 minutes"; interval = "1 day"; } 
            else if ("1w".equals(timeRange)) { bucket = "3 hours"; interval = "1 week"; }

            String query = """
                SELECT time_bucket(CAST(? AS interval), time) AS bucket_time, 
                       ROUND(AVG(temperature)::numeric, 2) AS avg_temp
                FROM sensor_data 
                WHERE time > NOW() - CAST(? AS interval)
                GROUP BY bucket_time
                ORDER BY bucket_time DESC
                """;

            List<String> labels = new ArrayList<>();
            List<Double> values = new ArrayList<>();

            try (Connection conn = DriverManager.getConnection("jdbc:postgresql://vessel_db:5432/vessel_data", "admin", "nikonasvrs");
                 PreparedStatement stmt = conn.prepareStatement(query)) {
                stmt.setString(1, bucket);
                stmt.setString(2, interval);
                ResultSet rs = stmt.executeQuery();
                while (rs.next()) {
                    String timeStr = rs.getString("bucket_time");
                    if (timeRange.equals("1h")) labels.add(timeStr.substring(11, 16)); 
                    else labels.add(timeStr.substring(8, 10) + "/" + timeStr.substring(5, 7) + " " + timeStr.substring(11, 16)); 
                    values.add(rs.getDouble("avg_temp"));
                }
            } catch (Exception e) {
                e.printStackTrace();
                ctx.status(500).result("Database Error");
                return;
            }
            Collections.reverse(labels);
            Collections.reverse(values);
            ctx.json(new TelemetryResponse(labels, values));
        });
        
        System.out.println("Το Java Edge API ξεκίνησε με WebSockets!");
    }

    private static void setupMqtt() {
        try {
            String broker = "tcp://mosquitto:1883"; 
            MqttClient client = new MqttClient(broker, "JavaBackendClient", null);
            MqttConnectOptions options = new MqttConnectOptions();
            options.setAutomaticReconnect(true);
            options.setCleanSession(true);
            client.connect(options);

            client.subscribe("vessel/ship_01/telemetry", (topic, msg) -> {
                String payload = new String(msg.getPayload());
                for (WsContext ws : clients) {
                    ws.send(payload);
                }
            });
            System.out.println("Συνδέθηκε στο MQTT και ακούει για δεδομένα...");
        } catch (Exception e) {
            System.out.println("Σφάλμα σύνδεσης στο MQTT: " + e.getMessage());
        }
    }

    record TelemetryResponse(List<String> labels, List<Double> values) {}
}
