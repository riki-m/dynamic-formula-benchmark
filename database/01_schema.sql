CREATE TABLE t_data (
    data_id INT PRIMARY KEY,
    a FLOAT NOT NULL,
    b FLOAT NOT NULL,
    c FLOAT NOT NULL,
    d FLOAT NOT NULL
);

CREATE TABLE t_targil (
    targil_id INT PRIMARY KEY,
    targil VARCHAR(255) NOT NULL,
    tnai VARCHAR(255) NULL,
    targil_false VARCHAR(255) NULL
);

CREATE TABLE t_results (
    result_id BIGINT PRIMARY KEY,
    data_id INT NOT NULL,
    targil_id INT NOT NULL,
    method VARCHAR(50) NOT NULL,
    result FLOAT NULL,
    CONSTRAINT fk_t_results_data
        FOREIGN KEY (data_id) REFERENCES t_data(data_id),
    CONSTRAINT fk_t_results_targil
        FOREIGN KEY (targil_id) REFERENCES t_targil(targil_id)
);

CREATE TABLE t_log (
    log_id INT PRIMARY KEY,
    targil_id INT NOT NULL,
    method VARCHAR(50) NOT NULL,
    run_time FLOAT NULL,
    records_processed INT NOT NULL,
    CONSTRAINT fk_t_log_targil
        FOREIGN KEY (targil_id) REFERENCES t_targil(targil_id)
);

CREATE INDEX idx_t_results_data_id ON t_results(data_id);
CREATE INDEX idx_t_results_targil_id ON t_results(targil_id);
CREATE INDEX idx_t_results_method ON t_results(method);
CREATE INDEX idx_t_log_targil_id ON t_log(targil_id);
CREATE INDEX idx_t_log_method ON t_log(method);
