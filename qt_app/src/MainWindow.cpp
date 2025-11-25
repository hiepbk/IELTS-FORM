#include "MainWindow.h"

#include <QApplication>
#include <algorithm>
#include <QClipboard>
#include <QDialog>
#include <QFileDialog>
#include <QFile>
#include <QFontDatabase>
#include <QHBoxLayout>
#include <QMessageBox>
#include <QPushButton>
#include <QRegularExpression>
#include <QScrollArea>
#include <QTextEdit>
#include <QTextStream>
#include <QVBoxLayout>

namespace {
constexpr int kNumQuestions = 40;

QVector<GroupSpec> listeningGroups() {
    QVector<GroupSpec> groups;
    for (int i = 0; i < 4; ++i) {
        const int start = i * 10 + 1;
        const int end = start + 9;
        groups.push_back(
            {QStringLiteral("Listening Part %1 (Q%2-%3)").arg(i + 1).arg(start).arg(end), 10});
    }
    return groups;
}

QVector<GroupSpec> readingGroups() {
    return {
        {"Reading Passage 1 (Q1-13)", 13},
        {"Reading Passage 2 (Q14-26)", 13},
        {"Reading Passage 3 (Q27-40)", 14},
    };
}

const QList<QPair<int, double>> listeningBandTable = {
    {39, 9.0}, {37, 8.5}, {35, 8.0}, {32, 7.5}, {30, 7.0},
    {26, 6.5}, {23, 6.0}, {18, 5.5}, {16, 5.0}, {13, 4.5},
    {11, 4.0}, {8, 3.5},  {6, 3.0},  {4, 2.5},  {0, 2.0},
};

const QList<QPair<int, double>> readingBandTable = {
    {39, 9.0}, {37, 8.5}, {35, 8.0}, {33, 7.5}, {30, 7.0},
    {27, 6.5}, {23, 6.0}, {19, 5.5}, {15, 5.0}, {13, 4.5},
    {10, 4.0}, {8, 3.5},  {6, 3.0},  {4, 2.5},  {0, 2.0},
};

QMap<int, QString> parseAnswerText(const QString &text) {
    QMap<int, QString> mapping;
    const QRegularExpression lineRe(R"(^\s*(\d+(?:&\d+)*)\s+(.+)$)");

    for (const QString &rawLine : text.split('\n')) {
        const QString line = rawLine.trimmed();
        if (line.isEmpty())
            continue;
        if (line.startsWith("part", Qt::CaseInsensitive) ||
            line.startsWith("passage", Qt::CaseInsensitive) ||
            line.startsWith('(')) {
            continue;
        }

        const QRegularExpressionMatch match = lineRe.match(line);
        if (!match.hasMatch())
            continue;

        const QString numbersToken = match.captured(1);
        const QString answersToken = match.captured(2).trimmed();
        if (answersToken.isEmpty())
            continue;

        const QStringList numberParts = numbersToken.split('&');
        QStringList answers = answersToken.split(QRegularExpression(R"(\s*,\s*)"),
                                                 Qt::SkipEmptyParts);
        if (answers.isEmpty()) {
            answers = QStringList{answersToken};
        }

        for (int i = 0; i < numberParts.size(); ++i) {
            bool ok = false;
            const int qNum = numberParts[i].toInt(&ok);
            if (!ok || qNum < 1 || qNum > kNumQuestions)
                continue;
            const QString answer = answers.value(i, answers.last());
            mapping[qNum] = answer.trimmed();
        }
    }

    return mapping;
}
} // namespace

MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent) {
    resize(900, 700);
    setWindowTitle(tr("IELTS Answer Form"));

    listeningPanel_ = new SectionPanel("Listening", listeningGroups(), this);
    readingPanel_ = new SectionPanel("Reading", readingGroups(), this);

    stack_ = new QStackedWidget(this);
    stack_->addWidget(buildLandingPage());
    stack_->addWidget(buildSectionPage(listeningPanel_));
    stack_->addWidget(buildSectionPage(readingPanel_));
    stack_->setCurrentIndex(0);

    auto *central = new QWidget(this);
    auto *layout = new QVBoxLayout(central);
    layout->setContentsMargins(16, 16, 16, 16);
    layout->addWidget(stack_);

    scoreLabel_ = new QLabel();
    scoreLabel_->setAlignment(Qt::AlignRight);
    layout->addWidget(scoreLabel_);

    auto *buttonRow = new QHBoxLayout();
    buttonRow->setSpacing(8);

    auto makeButton = [&](const QString &text, auto slot) {
        auto *btn = new QPushButton(text);
        connect(btn, &QPushButton::clicked, this, slot);
        buttonRow->addWidget(btn);
        return btn;
    };

    makeButton(tr("Submit"), &MainWindow::submitAnswers);
    makeButton(tr("Preview"), &MainWindow::previewAnswers);
    makeButton(tr("Clear All"), &MainWindow::clearActive);
    makeButton(tr("Save Answers"), &MainWindow::saveAnswers);

    auto *pasteBtn = new QPushButton(tr("Paste Right Answer"));
    connect(pasteBtn, &QPushButton::clicked, this, &MainWindow::pasteAnswerKeys);
    buttonRow->insertWidget(1, pasteBtn);

    hideButton_ = new QPushButton(tr("Hide Answers"));
    connect(hideButton_, &QPushButton::clicked, this, &MainWindow::toggleHideAnswers);
    buttonRow->insertWidget(2, hideButton_);

    layout->addLayout(buttonRow);

    setCentralWidget(central);
    applyKeyVisibility();
}

QWidget *MainWindow::buildLandingPage() {
    auto *page = new QWidget();
    auto *layout = new QVBoxLayout(page);
    layout->setAlignment(Qt::AlignCenter);

    auto *heading = new QLabel(tr("<b>Choose a test to begin</b>"));
    heading->setAlignment(Qt::AlignCenter);
    layout->addWidget(heading);

    auto *subtext = new QLabel(
        tr("Select Listening or Reading to load the corresponding answer sheet."));
    subtext->setAlignment(Qt::AlignCenter);
    subtext->setWordWrap(true);
    layout->addWidget(subtext);

    auto *buttonRow = new QHBoxLayout();
    buttonRow->setSpacing(32);

    auto makeCard = [&](const QString &text, const QColor &color, auto slot) {
        auto *btn = new QPushButton(text);
        btn->setMinimumSize(220, 160);
        btn->setStyleSheet(QStringLiteral(
            "font-weight: bold; font-size: 18px; color: white; border-radius: 16px;"
            "background-color: %1;").arg(color.name()));
        connect(btn, &QPushButton::clicked, this, slot);
        buttonRow->addWidget(btn);
    };

    makeCard(tr("Listening"), QColor("#27ae60"), &MainWindow::startListening);
    makeCard(tr("Reading"), QColor("#c0392b"), &MainWindow::startReading);

    layout->addLayout(buttonRow);
    return page;
}

QWidget *MainWindow::buildSectionPage(SectionPanel *panel) {
    auto *container = new QWidget();
    auto *layout = new QVBoxLayout(container);
    layout->setContentsMargins(0, 0, 0, 0);

    auto *backBtn = new QPushButton(tr("← Back"));
    backBtn->setFixedWidth(120);
    connect(backBtn, &QPushButton::clicked, this, &MainWindow::showLanding);
    layout->addWidget(backBtn, 0, Qt::AlignLeft);

    auto *scroll = new QScrollArea();
    scroll->setWidgetResizable(true);
    scroll->setWidget(panel);
    layout->addWidget(scroll);
    return container;
}

void MainWindow::showLanding() {
    stack_->setCurrentIndex(0);
    updateScoreLabel(QString());
}

void MainWindow::startListening() {
    stack_->setCurrentIndex(1);
    updateScoreLabel(QString());
}

void MainWindow::startReading() {
    stack_->setCurrentIndex(2);
    updateScoreLabel(QString());
}

SectionPanel *MainWindow::activePanel(QString *sectionName) const {
    int idx = stack_->currentIndex();
    if (idx == 1) {
        if (sectionName)
            *sectionName = QStringLiteral("Listening");
        return listeningPanel_;
    }
    if (idx == 2) {
        if (sectionName)
            *sectionName = QStringLiteral("Reading");
        return readingPanel_;
    }
    return nullptr;
}

void MainWindow::submitAnswers() {
    QString sectionName;
    SectionPanel *panel = activePanel(&sectionName);
    if (!panel) {
        QMessageBox::information(this, tr("Select a section"),
                                 tr("Choose Listening or Reading before submitting."));
        return;
    }
    const QStringList keys = panel->answerKeys();
    if (std::all_of(keys.begin(), keys.end(), [](const QString &k) { return k.isEmpty(); })) {
        QMessageBox::warning(this, tr("Missing answer keys"),
                             tr("Fill or paste the correct answers before submitting."));
        return;
    }
    const auto [correct, evaluated] = panel->evaluate();
    const double band = lookupBand(sectionName, correct);
    updateScoreLabel(
        tr("%1: %2/%3 correct · Band %4")
            .arg(sectionName)
            .arg(correct)
            .arg(panel->questionCount())
            .arg(QString::number(band, 'f', 1)));
}

void MainWindow::previewAnswers() {
    QString sectionName;
    SectionPanel *panel = activePanel(&sectionName);
    if (!panel) {
        QMessageBox::information(this, tr("Select a section"),
                                 tr("Choose Listening or Reading first."));
        return;
    }
    QStringList preview;
    const QStringList answers = panel->answers();
    for (int i = 0; i < answers.size(); ++i) {
        preview << QStringLiteral("Q%1: %2").arg(i + 1).arg(answers.at(i));
    }
    QMessageBox::information(this, tr("Preview"),
                             preview.join('\n'));
}

void MainWindow::clearActive() {
    SectionPanel *panel = activePanel();
    if (!panel) {
        QMessageBox::information(this, tr("Select a section"),
                                 tr("Choose Listening or Reading first."));
        return;
    }
    panel->clearAnswers();
    panel->clearKeys();
    updateScoreLabel(QString());
}

void MainWindow::saveAnswers() {
    QString sectionName;
    SectionPanel *panel = activePanel(&sectionName);
    if (!panel) {
        QMessageBox::information(this, tr("Select a section"),
                                 tr("Choose Listening or Reading first."));
        return;
    }
    const QString defaultName =
        QStringLiteral("ielts_%1_answers.txt").arg(sectionName.toLower());
    const QString filePath =
        QFileDialog::getSaveFileName(this, tr("Save answers"), defaultName,
                                     tr("Text Files (*.txt);;All Files (*)"));
    if (filePath.isEmpty())
        return;

    QFile file(filePath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QMessageBox::critical(this, tr("Unable to save"),
                              tr("Could not write to %1").arg(filePath));
        return;
    }
    QTextStream out(&file);
    const QStringList answers = panel->answers();
    out << sectionName << '\n';
    for (int i = 0; i < answers.size(); ++i) {
        out << (i + 1) << "," << answers.at(i) << '\n';
    }
    file.close();
}

void MainWindow::pasteAnswerKeys() {
    SectionPanel *panel = activePanel();
    if (!panel) {
        QMessageBox::information(this, tr("Select a section"),
                                 tr("Choose Listening or Reading first."));
        return;
    }

    QDialog dialog(this);
    dialog.setWindowTitle(tr("Paste Right Answer"));
    dialog.resize(500, 400);

    auto *layout = new QVBoxLayout(&dialog);
    auto *label = new QLabel(
        tr("Paste the answer list (e.g., '21&22   A, E'). One question per line."));
    label->setWordWrap(true);
    layout->addWidget(label);

    auto *editor = new QTextEdit();
    editor->setPlainText(QApplication::clipboard()->text());
    layout->addWidget(editor);

    auto *buttonRow = new QHBoxLayout();
    buttonRow->addStretch();
    auto *cancel = new QPushButton(tr("Cancel"));
    auto *apply = new QPushButton(tr("Apply"));
    buttonRow->addWidget(cancel);
    buttonRow->addWidget(apply);
    layout->addLayout(buttonRow);

    connect(cancel, &QPushButton::clicked, &dialog, &QDialog::reject);
    connect(apply, &QPushButton::clicked, &dialog, &QDialog::accept);

    if (dialog.exec() != QDialog::Accepted)
        return;

    const QMap<int, QString> mapping = parseAnswerText(editor->toPlainText());
    if (mapping.isEmpty()) {
        QMessageBox::warning(this, tr("No answers detected"),
                             tr("Make sure the text contains numbered lines."));
        return;
    }
    panel->applyParsedAnswers(mapping);
    updateScoreLabel(QString());
}

void MainWindow::toggleHideAnswers() {
    answersHidden_ = !answersHidden_;
    applyKeyVisibility();
}

double MainWindow::lookupBand(const QString &sectionName, int correct) const {
    const auto &table = sectionName == "Listening" ? listeningBandTable : readingBandTable;
    for (const auto &pair : table) {
        if (correct >= pair.first)
            return pair.second;
    }
    return 0.0;
}

void MainWindow::updateScoreLabel(const QString &text) {
    scoreLabel_->setText(text);
}

void MainWindow::applyKeyVisibility() {
    const bool visible = !answersHidden_;
    hideButton_->setText(visible ? tr("Hide Answers") : tr("Show Answers"));
    listeningPanel_->setKeysVisible(visible);
    readingPanel_->setKeysVisible(visible);
}

