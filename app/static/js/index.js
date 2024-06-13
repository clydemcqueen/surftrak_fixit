// Extension + mavlink2rest + ArduSub status
let el_system_status = document.getElementById("system_status");

// DISTANCE_SENSOR status
let el_info_ping_detected = document.getElementById("info_ping_detected");
let el_info_wl_dvl_detected = document.getElementById("info_wl_dvl_detected");

// Errors
let el_prb_not_configured = document.getElementById("prb_not_configured");
let el_prb_no_sensor_msgs = document.getElementById("prb_no_sensor_msgs");
let el_prb_too_many_sensor_msgs = document.getElementById("prb_too_many_sensor_msgs");
let el_prb_rangefinder_timeout = document.getElementById("prb_rangefinder_timeout");
let el_prb_global_position_int_timeout = document.getElementById("prb_global_position_int_timeout");
let el_prb_bad_orient = document.getElementById("prb_bad_orient");

// Warnings
let el_prb_bad_max = document.getElementById("prb_bad_max");
let el_prb_bad_kpv = document.getElementById("prb_bad_kpv");
let el_prb_no_btn = document.getElementById("prb_no_btn");

// Key state values
let el_relative_alt_m_card = document.getElementById("relative_alt_m_card");
let el_rf_target_m_card = document.getElementById("rf_target_m_card");
let el_rangefinder_m_card = document.getElementById("rangefinder_m_card");
let el_seafloor_alt_m_card = document.getElementById("seafloor_alt_m_card");

// Interesting parameter values
let el_rngfnd1_type_card = document.getElementById("rngfnd1_type_card");
let el_rngfnd1_max_cm_card = document.getElementById("rngfnd1_max_cm_card");
let el_rngfnd1_min_cm_card = document.getElementById("rngfnd1_min_cm_card");
let el_rngfnd1_orient_card = document.getElementById("rngfnd1_orient_card");
let el_surftrak_depth_card = document.getElementById("surftrak_depth_card");
let el_psc_jerk_z_card = document.getElementById("psc_jerk_z_card");
let el_pilot_accel_z_card = document.getElementById("pilot_accel_z_card");
let el_btn_surftrak_card = document.getElementById("btn_surftrak_card");

const default_json = {
    "ok" : false,
    "info_ping_detected" : false,
    "info_wl_dvl_detected" : false,
    "prb_not_configured" : false,
    "prb_no_sensor_msgs" : false,
    "prb_too_many_sensor_msgs" : false,
    "prb_rangefinder_timeout" : false,
    "prb_global_position_int_timeout" : false,
    "prb_bad_orient" : false,
    "prb_bad_max" : false,
    "prb_bad_kpv" : false,
    "prb_no_btn" : false,
    "relative_alt_m" : null,
    "rf_target_m" : null,
    "rangefinder_m" : null,
    "rngfnd1_type" : null,
    "rngfnd1_max_cm" : null,
    "rngfnd1_min_cm" : null,
    "rngfnd1_orient" : null,
    "surftrak_depth" : null,
    "psc_jerk_z" : null,
    "pilot_accel_z" : null,
    "btn_surftrak" : null,
}

async function getStatus() {
    let system_status_text = "The extension is not responding";
    let system_status_class = "status-error"
    let response_ok = false;
    let response_json = default_json;

    // Get the latest status
    try {
        const response = await fetch("/status");
        if (response.ok) {
            response_ok = true;
            response_json = await response.json();
        }
    } catch (ex) {
        console.error(ex)
    }

    const {
        ok,
        info_ping_detected,
        info_wl_dvl_detected,
        prb_not_configured,
        prb_no_sensor_msgs,
        prb_too_many_sensor_msgs,
        prb_rangefinder_timeout,
        prb_global_position_int_timeout,
        prb_bad_orient,
        prb_bad_max,
        prb_bad_kpv,
        prb_no_btn,
        relative_alt_m,
        rf_target_m,
        rangefinder_m,
        rngfnd1_type,
        rngfnd1_max_cm,
        rngfnd1_min_cm,
        rngfnd1_orient,
        surftrak_depth,
        psc_jerk_z,
        pilot_accel_z,
        btn_surftrak,
    } = response_json;

    if (ok) {
        system_status_text = "ArduSub is running"
        system_status_class = "status-good"
    } else if (response_ok) {
        system_status_text = "ArduSub is not responding";
    }

    el_info_ping_detected.className = info_ping_detected ? "status-good" : "status-hidden";
    el_info_wl_dvl_detected.className = info_wl_dvl_detected ? "status-good" : "status-hidden";

    el_prb_not_configured.className = prb_not_configured ? "status-error" : "status-hidden";
    el_prb_no_sensor_msgs.className = prb_no_sensor_msgs ? "status-error" : "status-hidden";
    el_prb_too_many_sensor_msgs.className = prb_too_many_sensor_msgs ? "status-error" : "status-hidden";
    el_prb_rangefinder_timeout.className = prb_rangefinder_timeout ? "status-error" : "status-hidden";
    el_prb_global_position_int_timeout.className = prb_global_position_int_timeout ? "status-error" : "status-hidden";
    el_prb_bad_orient.className = prb_bad_orient ? "status-error" : "status-hidden";

    el_prb_bad_max.className = prb_bad_max ? "status-warning" : "status-hidden";
    el_prb_bad_kpv.className = prb_bad_kpv ? "status-warning" : "status-hidden";
    el_prb_no_btn.className = prb_no_btn ? "status-warning" : "status-hidden";

    el_relative_alt_m_card.textContent = relative_alt_m != null ? relative_alt_m.toFixed(2) : "Unknown";
    el_rf_target_m_card.textContent = rf_target_m != null && rf_target_m > 0 ? rf_target_m.toFixed(2) : "No target";
    el_rangefinder_m_card.textContent = rangefinder_m != null ? rangefinder_m.toFixed(2) : "No rangefinder";
    el_seafloor_alt_m_card.textContent = relative_alt_m != null && rangefinder_m != null ? (relative_alt_m - rangefinder_m).toFixed(2) : "Unknown";

    el_rngfnd1_type_card.textContent = rngfnd1_type === null ? "Unknown" : rngfnd1_type;
    el_rngfnd1_max_cm_card.textContent = rngfnd1_max_cm === null ? "Unknown" : rngfnd1_max_cm;
    el_rngfnd1_min_cm_card.textContent = rngfnd1_min_cm === null ? "Unknown" : rngfnd1_min_cm;
    el_rngfnd1_orient_card.textContent = rngfnd1_orient === null ? "Unknown" : rngfnd1_orient;
    el_surftrak_depth_card.textContent = surftrak_depth === null ? "Unknown" : surftrak_depth;
    el_psc_jerk_z_card.textContent = psc_jerk_z === null ? "Unknown" : psc_jerk_z;
    el_pilot_accel_z_card.textContent = pilot_accel_z === null ? "Unknown" : pilot_accel_z;
    el_btn_surftrak_card.textContent = btn_surftrak === null ? "No assignment" : btn_surftrak;

    el_system_status.textContent = system_status_text;
    el_system_status.className = system_status_class;
}

setInterval(getStatus, 500);
