#include "SectionPanel.h"

#include <QHBoxLayout>
#include <QRegularExpression>
#include <QVBoxLayout>

namespace {
QString normalizeAnswer(const QString &raw) {
    QString cleaned = raw.trimmed().toLower();
    static const QRegularExpression re(R"([\s\-]+)");
    cleaned.replace(re, "");
    return cleaned;
}
} // namespace

SectionPanel::SectionPanel(const QString &sectionName,
                           const QVector<GroupSpec> &groups,
                           QWidget *parent)
    : QWidget(parent), sectionName_(sectionName), groups_(groups) {
    buildGrid();
}

void SectionPanel::buildGrid() {
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);

    auto *grid = new QGridLayout();
    grid->setVerticalSpacing(6);
    grid->setHorizontalSpacing(24);

    int column = 0;
    int questionNumber = 1;

    for (const auto &group : groups_) {
        auto *header = new QLabel(QStringLiteral("<b>%1</b>").arg(group.title));
        grid->addWidget(header, 0, column, Qt::AlignLeft);

        for (int row = 0; row < group.count; ++row) {
            const int qNum = questionNumber + row;
            auto *cell = new QWidget();
            auto *cellLayout = new QHBoxLayout(cell);
            cellLayout->setContentsMargins(0, 0, 0, 0);
            cellLayout->setSpacing(4);

            auto *numberLabel =
                new QLabel(QStringLiteral("%1.").arg(qNum));
            numberLabel->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
            numberLabel->setMinimumWidth(24);

            auto *user = new QLineEdit();
            user->setMaxLength(32);
            user->setFixedWidth(90);

            auto *answerKey = new QLineEdit();
            answerKey->setPlaceholderText(QStringLiteral("Answer"));
            answerKey->setMaxLength(32);
            answerKey->setFixedWidth(90);

            auto *status = new QLabel();
            status->setFixedWidth(16);

            cellLayout->addWidget(numberLabel);
            cellLayout->addWidget(user);
            cellLayout->addWidget(answerKey);
            cellLayout->addWidget(status);

            grid->addWidget(cell, row + 1, column);

            userEdits_.append(user);
            keyEdits_.append(answerKey);
            statusLabels_.append(status);
        }

        questionNumber += group.count;
        ++column;
    }

    layout->addLayout(grid);
    layout->addStretch();
}

QStringList SectionPanel::answers() const {
    QStringList list;
    list.reserve(userEdits_.size());
    for (const auto *edit : userEdits_) {
        list << edit->text().trimmed();
    }
    return list;
}

QStringList SectionPanel::answerKeys() const {
    QStringList list;
    list.reserve(keyEdits_.size());
    for (const auto *edit : keyEdits_) {
        list << edit->text().trimmed();
    }
    return list;
}

int SectionPanel::questionCount() const {
    return userEdits_.size();
}

void SectionPanel::clearAnswers() {
    for (auto *edit : userEdits_) {
        edit->clear();
    }
    resetFeedback();
}

void SectionPanel::clearKeys() {
    for (auto *edit : keyEdits_) {
        edit->clear();
    }
    resetFeedback();
}

void SectionPanel::resetFeedback() {
    for (auto *label : statusLabels_) {
        label->clear();
    }
}

QPair<int, int> SectionPanel::evaluate() {
    int correct = 0;
    int evaluated = 0;
    const int total = userEdits_.size();
    for (int i = 0; i < total; ++i) {
        auto *status = statusLabels_[i];
        const QString key = keyEdits_[i]->text().trimmed();
        if (key.isEmpty()) {
            status->clear();
            continue;
        }
        ++evaluated;
        const QString user = userEdits_[i]->text().trimmed();
        const bool ok = normalizeAnswer(user) == normalizeAnswer(key);
        const QString symbol = ok ? QStringLiteral("✓") : QStringLiteral("✗");
        const QString color = ok ? QStringLiteral("green") : QStringLiteral("red");
        status->setText(QStringLiteral("<font color='%1'>%2</font>").arg(color, symbol));
        if (ok) {
            ++correct;
        }
    }
    return {correct, evaluated};
}

void SectionPanel::setKeysVisible(bool visible) {
    keysVisible_ = visible;
    const auto mode = visible ? QLineEdit::Normal : QLineEdit::Password;
    for (auto *edit : keyEdits_) {
        edit->setEchoMode(mode);
    }
}

void SectionPanel::applyParsedAnswers(const QMap<int, QString> &mapping) {
    int index = 0;
    for (auto *edit : keyEdits_) {
        const int questionNumber = index + 1;
        if (mapping.contains(questionNumber)) {
            edit->setText(mapping.value(questionNumber));
        }
        ++index;
    }
    resetFeedback();
}

