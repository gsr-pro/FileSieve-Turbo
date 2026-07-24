import sys
import os
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QGridLayout
)
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl

# Importar os módulos
import OrganizaDestino_extensao as ext_module
import OrganizaDestino_por_tipo as tipo_module

# Importar workers
from workers import LogHandler, WorkerThread, SearchWorkerThread, CopyWorkerThread

# Janela principal
class OrganizadorMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organizador de Arquivos - Nível Ouro")
        self.setGeometry(100, 100, 1100, 800)

        # Configurar logger
        self.log_handler_ext = LogHandler()
        self.log_handler_tipo = LogHandler()
        self.root_logger = logging.getLogger()
        self.original_handlers = self.root_logger.handlers.copy()

        # Criar abas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Aba 1: Organizar por Extensão
        self.tab_ext = self.create_tab_extensao()
        self.tabs.addTab(self.tab_ext, "📂 Por Extensão")

        # Aba 2: Organizar por Tipo
        self.tab_tipo = self.create_tab_tipo()
        self.tabs.addTab(self.tab_tipo, "📑 Por Tipo")

        # Aba 3: Busca XML
        self.tab_busca = self.create_tab_busca_xml()
        self.tabs.addTab(self.tab_busca, "🔍 Busca XML")

    def create_tab_extensao(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Grupo de descrição
        desc_group = QGroupBox("Descrição")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(
            "📄 Organiza arquivos por extensão (ex: .pdf, .xlsx, .xml).\n"
            "🔹 Extrai arquivos .zip e .rar recursivamente.\n"
            "🔹 Usa sharding para evitar pastas com muitos arquivos.\n"
            "🔹 Limpa pastas vazias após organização."
        )
        desc_label.setFont(QFont("Arial", 10))
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)

        # Grupo de seleção de pasta
        path_group = QGroupBox("Selecionar Pasta")
        path_layout = QHBoxLayout(path_group)
        self.path_ext_edit = QLineEdit()
        self.path_ext_edit.setPlaceholderText("Caminho da pasta de destino...")
        btn_browse_ext = QPushButton("Procurar...")
        btn_browse_ext.clicked.connect(self.browse_ext)
        path_layout.addWidget(self.path_ext_edit)
        path_layout.addWidget(btn_browse_ext)
        layout.addWidget(path_group)

        # Botão iniciar
        self.btn_start_ext = QPushButton("🚀 Iniciar Organização por Extensão")
        self.btn_start_ext.clicked.connect(self.start_extensao)
        layout.addWidget(self.btn_start_ext)

        # Log
        log_group = QGroupBox("Log de Execução")
        log_layout = QVBoxLayout(log_group)
        self.log_ext_text = QTextEdit()
        self.log_ext_text.setReadOnly(True)
        log_layout.addWidget(self.log_ext_text)
        layout.addWidget(log_group)

        # Conectar o handler de log
        self.log_handler_ext.log_signal.connect(self.append_log_ext)

        return widget

    def create_tab_tipo(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Grupo de descrição
        desc_group = QGroupBox("Descrição")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(
            "📄 Classifica arquivos por conteúdo (não só extensão):\n"
            "🔹 SPED TXT: ECD, ECF, EFD ICMS IPI, EFD Contribuições, EFD Reinf\n"
            "🔹 XML: NFe, CTe, NFSe Nacional/Municipal, Eventos, Inutilizados\n"
            "🔹 Tratamento de erros: envia arquivos inválidos ou não identificados para 'Nao_Identificados'\n"
            "🔹 Extrai arquivos .zip e .rar recursivamente\n"
            "🔹 Usa sharding para evitar pastas com muitos arquivos\n"
            "🔹 Limpa pastas vazias após organização"
        )
        desc_label.setFont(QFont("Arial", 10))
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)

        # Grupo de seleção de pasta
        path_group = QGroupBox("Selecionar Pasta")
        path_layout = QHBoxLayout(path_group)
        self.path_tipo_edit = QLineEdit()
        self.path_tipo_edit.setPlaceholderText("Caminho da pasta de destino...")
        btn_browse_tipo = QPushButton("Procurar...")
        btn_browse_tipo.clicked.connect(self.browse_tipo)
        path_layout.addWidget(self.path_tipo_edit)
        path_layout.addWidget(btn_browse_tipo)
        layout.addWidget(path_group)

        # Botão iniciar
        self.btn_start_tipo = QPushButton("🚀 Iniciar Organização por Tipo")
        self.btn_start_tipo.clicked.connect(self.start_tipo)
        layout.addWidget(self.btn_start_tipo)

        # Log
        log_group = QGroupBox("Log de Execução")
        log_layout = QVBoxLayout(log_group)
        self.log_tipo_text = QTextEdit()
        self.log_tipo_text.setReadOnly(True)
        log_layout.addWidget(self.log_tipo_text)
        layout.addWidget(log_group)

        # Conectar o handler de log
        self.log_handler_tipo.log_signal.connect(self.append_log_tipo)

        return widget

    def create_tab_busca_xml(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Grupo de descrição
        desc_group = QGroupBox("Descrição")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(
            "🔍 Busca arquivos XML por Chave de Acesso, Número do Documento e/ou CNPJ.\n"
            "🔹 Preencha um ou mais campos para filtrar.\n"
            "🔹 Clique duas vezes no resultado para abrir o arquivo."
        )
        desc_label.setFont(QFont("Arial", 10))
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)

        # Grupo de configuração da busca
        config_group = QGroupBox("Configuração da Busca")
        config_layout = QVBoxLayout(config_group)

        # Pasta de busca
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Pasta de Busca:"))
        self.path_busca_edit = QLineEdit()
        self.path_busca_edit.setPlaceholderText("Selecione a pasta para buscar os arquivos XML...")
        path_layout.addWidget(self.path_busca_edit)
        btn_browse_busca = QPushButton("📂 Procurar...")
        btn_browse_busca.clicked.connect(self.browse_busca)
        path_layout.addWidget(btn_browse_busca)
        config_layout.addLayout(path_layout)

        # Critérios de busca
        criteria_layout = QGridLayout()
        criteria_layout.addWidget(QLabel("Chave de Acesso:"), 0, 0)
        self.chave_acesso_edit = QLineEdit()
        self.chave_acesso_edit.setPlaceholderText("Digite a chave de acesso (44 dígitos)...")
        criteria_layout.addWidget(self.chave_acesso_edit, 0, 1)
        criteria_layout.addWidget(QLabel("Número do Documento:"), 1, 0)
        self.numero_doc_edit = QLineEdit()
        self.numero_doc_edit.setPlaceholderText("Digite o número do documento...")
        criteria_layout.addWidget(self.numero_doc_edit, 1, 1)
        criteria_layout.addWidget(QLabel("CNPJ:"), 2, 0)
        self.cnpj_edit = QLineEdit()
        self.cnpj_edit.setPlaceholderText("Digite o CNPJ (14 dígitos)...")
        criteria_layout.addWidget(self.cnpj_edit, 2, 1)
        config_layout.addLayout(criteria_layout)

        # Botão buscar
        self.btn_buscar = QPushButton("🔍 Iniciar Busca")
        self.btn_buscar.setStyleSheet("padding: 8px; font-size: 12px; font-weight: bold;")
        self.btn_buscar.clicked.connect(self.start_busca)
        config_layout.addWidget(self.btn_buscar)

        layout.addWidget(config_group)

        # Grupo de status e progresso
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        self.progress_label = QLabel("✅ Aguardando busca...")
        self.progress_label.setStyleSheet("font-size: 12px; padding: 5px;")
        status_layout.addWidget(self.progress_label)
        layout.addWidget(status_group)

        # Tabela de resultados
        result_group = QGroupBox("Resultados da Busca")
        result_layout = QVBoxLayout(result_group)
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(1)
        self.result_table.setHorizontalHeaderLabels(["Caminho do Arquivo"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.cellDoubleClicked.connect(self.open_file)
        result_layout.addWidget(self.result_table)
        layout.addWidget(result_group)

        # Grupo de ações com os resultados
        actions_group = QGroupBox("Ações com Resultados")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(QLabel("Pasta de Destino para Cópia:"))
        self.copy_dest_edit = QLineEdit()
        self.copy_dest_edit.setPlaceholderText("Selecione onde salvar os arquivos copiados...")
        actions_layout.addWidget(self.copy_dest_edit)
        btn_browse_copy = QPushButton("📂 Procurar...")
        btn_browse_copy.clicked.connect(self.browse_copy_dest)
        actions_layout.addWidget(btn_browse_copy)
        self.btn_copiar = QPushButton("📋 Copiar Arquivos Encontrados")
        self.btn_copiar.setStyleSheet("padding: 8px; font-size: 12px;")
        self.btn_copiar.clicked.connect(self.start_copy)
        self.btn_copiar.setEnabled(False)
        actions_layout.addWidget(self.btn_copiar)
        layout.addWidget(actions_group)

        return widget

    def browse_ext(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a Pasta")
        if dir_path:
            self.path_ext_edit.setText(dir_path)

    def browse_tipo(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a Pasta")
        if dir_path:
            self.path_tipo_edit.setText(dir_path)

    def browse_busca(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a Pasta para Busca")
        if dir_path:
            self.path_busca_edit.setText(dir_path)

    def browse_copy_dest(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecione a Pasta para Copiar os Arquivos")
        if dir_path:
            self.copy_dest_edit.setText(dir_path)

    def start_extensao(self):
        path = self.path_ext_edit.text().strip()
        if not path or not os.path.isdir(path):
            self.append_log_ext("⚠️ Por favor, selecione uma pasta válida!")
            return

        # Configurar logger
        self.root_logger.handlers = [self.log_handler_ext]

        # Desativar botão
        self.btn_start_ext.setEnabled(False)
        self.btn_start_ext.setText("⏳ Processando...")

        # Criar e iniciar thread
        self.worker_ext = WorkerThread(ext_module.executar_somente_destino, path)
        self.worker_ext.finished.connect(lambda: self.on_finished_ext())
        self.worker_ext.error.connect(lambda e: self.append_log_ext(f"❌ Erro: {e}"))
        self.worker_ext.start()

    def start_tipo(self):
        path = self.path_tipo_edit.text().strip()
        if not path or not os.path.isdir(path):
            self.append_log_tipo("⚠️ Por favor, selecione uma pasta válida!")
            return

        # Configurar logger
        self.root_logger.handlers = [self.log_handler_tipo]

        # Desativar botão
        self.btn_start_tipo.setEnabled(False)
        self.btn_start_tipo.setText("⏳ Processando...")

        # Criar e iniciar thread
        self.worker_tipo = WorkerThread(tipo_module.executar_organizar_por_tipo, path)
        self.worker_tipo.finished.connect(lambda: self.on_finished_tipo())
        self.worker_tipo.error.connect(lambda e: self.append_log_tipo(f"❌ Erro: {e}"))
        self.worker_tipo.start()

    def start_busca(self):
        path = self.path_busca_edit.text().strip()
        if not path or not os.path.isdir(path):
            self.progress_label.setText("⚠️ Por favor, selecione uma pasta válida!")
            return

        chave = self.chave_acesso_edit.text()
        numero = self.numero_doc_edit.text()
        cnpj = self.cnpj_edit.text()

        if not chave and not numero and not cnpj:
            self.progress_label.setText("⚠️ Por favor, preencha pelo menos um critério de busca!")
            return

        # Limpar tabela
        self.result_table.setRowCount(0)

        # Desativar botão
        self.btn_buscar.setEnabled(False)
        self.btn_buscar.setText("⏳ Buscando...")
        self.progress_label.setText("🔍 Varrendo diretórios...")

        # Criar e iniciar thread de busca
        self.worker_busca = SearchWorkerThread(path, chave, numero, cnpj)
        self.worker_busca.found_file.connect(self.add_result)
        self.worker_busca.progress.connect(self.update_progress)
        self.worker_busca.error.connect(lambda e: self.progress_label.setText(f"❌ Erro: {e}"))
        self.worker_busca.finished.connect(lambda: self.on_finished_busca())
        self.worker_busca.start()

    def add_result(self, file_path):
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        self.result_table.setItem(row, 0, QTableWidgetItem(file_path))

    def update_progress(self, processed, scanned, found):
        if scanned == -1:
            self.progress_label.setText("🔍 Iniciando varredura de arquivos na pasta...")
        else:
            self.progress_label.setText(f"🔍 Varridos: {scanned} | Analisados (XML): {processed} | Encontrados: {found}")

    def open_file(self, row, column):
        file_path = self.result_table.item(row, column).text()
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def on_finished_busca(self):
        self.btn_buscar.setEnabled(True)
        self.btn_buscar.setText("🔍 Buscar")
        count = self.result_table.rowCount()
        self.progress_label.setText(f"✅ Busca concluída! {count} arquivo(s) encontrado(s).")
        self.btn_copiar.setEnabled(count > 0)

    def start_copy(self):
        dest_path = self.copy_dest_edit.text().strip()
        if not dest_path or not os.path.isdir(dest_path):
            self.progress_label.setText("⚠️ Por favor, selecione uma pasta de destino válida!")
            return

        # Coletar lista de arquivos da tabela
        file_list = []
        for row in range(self.result_table.rowCount()):
            file_list.append(self.result_table.item(row, 0).text())

        if not file_list:
            self.progress_label.setText("⚠️ Nenhum arquivo para copiar!")
            return

        # Desativar botão
        self.btn_copiar.setEnabled(False)
        self.btn_copiar.setText("⏳ Copiando...")

        # Criar e iniciar thread de cópia
        self.worker_copy = CopyWorkerThread(file_list, dest_path)
        self.worker_copy.copy_progress.connect(self.update_copy_progress)
        self.worker_copy.error.connect(lambda e: self.progress_label.setText(f"❌ Erro: {e}"))
        self.worker_copy.finished.connect(lambda: self.on_finished_copy(len(file_list)))
        self.worker_copy.start()

    def update_copy_progress(self, copied, total):
        percent = int((copied / total) * 100)
        self.progress_label.setText(f"📋 Copiando... {copied}/{total} arquivos ({percent}%)")

    def on_finished_copy(self, total):
        self.btn_copiar.setEnabled(True)
        self.btn_copiar.setText("📋 Copiar Arquivos Encontrados")
        self.progress_label.setText(f"✅ Cópia concluída! {total} arquivo(s) copiado(s).")

    def append_log_ext(self, msg):
        self.log_ext_text.append(msg)

    def append_log_tipo(self, msg):
        self.log_tipo_text.append(msg)

    def on_finished_ext(self):
        self.btn_start_ext.setEnabled(True)
        self.btn_start_ext.setText("🚀 Iniciar Organização por Extensão")
        self.root_logger.handlers = self.original_handlers.copy()

    def on_finished_tipo(self):
        self.btn_start_tipo.setEnabled(True)
        self.btn_start_tipo.setText("🚀 Iniciar Organização por Tipo")
        self.root_logger.handlers = self.original_handlers.copy()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OrganizadorMainWindow()
    window.show()
    sys.exit(app.exec())
